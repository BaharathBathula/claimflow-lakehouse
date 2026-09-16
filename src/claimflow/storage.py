from __future__ import annotations

import json
import sqlite3
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq


class EventLedger:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS processed_events "
            "(event_id TEXT PRIMARY KEY, processed_at TEXT DEFAULT CURRENT_TIMESTAMP)"
        )
        self.connection.commit()

    def contains(self, event_id: str) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM processed_events WHERE event_id = ?", (event_id,)
        ).fetchone()
        return row is not None

    def mark_many(self, event_ids: list[str]) -> None:
        self.connection.executemany(
            "INSERT OR IGNORE INTO processed_events(event_id) VALUES (?)",
            [(event_id,) for event_id in event_ids],
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()


class BronzeWriter:
    def __init__(self, root: Path) -> None:
        self.root = root

    def write(self, rows: list[dict[str, Any]]) -> list[Path]:
        grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[(row.pop("_entity"), row.pop("_event_date"))].append(row)

        outputs: list[Path] = []
        for (entity, event_date), records in grouped.items():
            target = self.root / f"entity={entity}" / f"event_date={event_date}"
            target.mkdir(parents=True, exist_ok=True)
            path = target / f"part-{uuid.uuid4().hex}.parquet"
            table = pa.Table.from_pylist(records)
            pq.write_table(table, path, compression="zstd", use_dictionary=True)
            outputs.append(path)
        return outputs


class DeadLetterWriter:
    def __init__(self, path: Path) -> None:
        self.path = path

    def write(self, raw: Any, reason: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"reason": reason, "raw": raw}, default=str) + "\n")
