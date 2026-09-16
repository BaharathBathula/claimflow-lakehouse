import json

import pyarrow.parquet as pq

from claimflow.generator import generate_events
from claimflow.ingest import BatchProcessor


def _processor(tmp_path):
    return BatchProcessor(
        bronze_root=tmp_path / "bronze",
        ledger_path=tmp_path / "state" / "ledger.sqlite",
        dlq_path=tmp_path / "dlq" / "invalid.ndjson",
    )


def test_ingestion_writes_parquet_and_is_idempotent(tmp_path) -> None:
    event = next(generate_events(20))
    record = event.model_dump(mode="json")
    processor = _processor(tmp_path)

    first = processor.process([record])
    second = processor.process([record])
    processor.close()

    assert first.accepted == 1
    assert first.files_written == 1
    assert second.accepted == 0
    assert second.duplicates == 1

    parquet_file = next((tmp_path / "bronze").glob("entity=policy/**/*.parquet"))
    columns = pq.read_schema(parquet_file).names
    assert "customer_name" not in columns
    assert "customer_email" not in columns
    assert "customer_name_token" in columns


def test_invalid_event_is_quarantined(tmp_path) -> None:
    event = next(generate_events(20)).model_dump(mode="json")
    del event["payload"]["policy_id"]
    processor = _processor(tmp_path)

    result = processor.process([json.dumps(event)])
    processor.close()

    assert result.rejected == 1
    dlq = tmp_path / "dlq" / "invalid.ndjson"
    assert dlq.exists()
    assert "policy_id" in dlq.read_text()
