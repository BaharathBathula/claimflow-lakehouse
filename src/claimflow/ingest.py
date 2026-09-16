from __future__ import annotations

import json
import time
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from claimflow.metrics import (
    EVENTS_ACCEPTED,
    EVENTS_DUPLICATE,
    EVENTS_REJECTED,
    INGEST_LATENCY,
    LAST_EVENT_EPOCH,
)
from claimflow.models import EventEnvelope, validate_payload
from claimflow.security import protect_pii
from claimflow.storage import BronzeWriter, DeadLetterWriter, EventLedger


@dataclass
class IngestResult:
    accepted: int = 0
    rejected: int = 0
    duplicates: int = 0
    files_written: int = 0


def _serializable(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


class BatchProcessor:
    def __init__(
        self,
        bronze_root: Path = Path("data/lake/bronze"),
        ledger_path: Path = Path("data/lake/bronze/_state/ledger.sqlite"),
        dlq_path: Path = Path("data/dlq/invalid-events.ndjson"),
    ) -> None:
        self.writer = BronzeWriter(bronze_root)
        self.ledger = EventLedger(ledger_path)
        self.dlq = DeadLetterWriter(dlq_path)

    def process(self, records: Iterable[str | bytes | dict[str, Any]]) -> IngestResult:
        started = time.perf_counter()
        result = IngestResult()
        rows: list[dict[str, Any]] = []
        accepted_ids: list[str] = []

        for raw in records:
            parsed: Any = raw
            try:
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8")
                if isinstance(raw, str):
                    parsed = json.loads(raw)
                envelope = EventEnvelope.model_validate(parsed)
                if self.ledger.contains(envelope.event_id):
                    result.duplicates += 1
                    EVENTS_DUPLICATE.inc()
                    continue

                payload = validate_payload(envelope).model_dump(mode="python")
                protected = {
                    key: _serializable(value) for key, value in protect_pii(payload).items()
                }
                entity = envelope.event_type.split(".", maxsplit=1)[0]
                rows.append(
                    {
                        "_entity": entity,
                        "_event_date": envelope.occurred_at.date().isoformat(),
                        "event_id": envelope.event_id,
                        "event_type": envelope.event_type,
                        "event_version": envelope.event_version,
                        "occurred_at": envelope.occurred_at,
                        "producer": envelope.producer,
                        "correlation_id": envelope.correlation_id,
                        "ingested_at": datetime.now().astimezone(),
                        **protected,
                    }
                )
                accepted_ids.append(envelope.event_id)
                result.accepted += 1
                EVENTS_ACCEPTED.labels(entity=entity).inc()
                LAST_EVENT_EPOCH.set(envelope.occurred_at.timestamp())
            except (json.JSONDecodeError, ValidationError, ValueError, TypeError) as exc:
                result.rejected += 1
                reason = type(exc).__name__
                EVENTS_REJECTED.labels(reason=reason).inc()
                self.dlq.write(parsed, str(exc))

        if rows:
            result.files_written = len(self.writer.write(rows))
            # At-least-once writes are followed by ledger acknowledgement. dbt models also
            # deduplicate on event_id, protecting the pipeline from a crash between these steps.
            self.ledger.mark_many(accepted_ids)
        INGEST_LATENCY.observe(time.perf_counter() - started)
        return result

    def close(self) -> None:
        self.ledger.close()


def read_ndjson(path: Path) -> Iterable[str]:
    with path.open(encoding="utf-8") as handle:
        yield from handle
