from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from claimflow.ingest import BatchProcessor

console = Console()


def records_between(path: Path, start: datetime, end: datetime) -> Iterable[dict]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            occurred_at = datetime.fromisoformat(record["occurred_at"].replace("Z", "+00:00"))
            if start <= occurred_at < end:
                yield record


def main(
    archive: Path,
    start: Annotated[datetime, typer.Option(formats=["%Y-%m-%dT%H:%M:%S%z"])],
    end: Annotated[datetime, typer.Option(formats=["%Y-%m-%dT%H:%M:%S%z"])],
) -> None:
    """Replay a bounded event-time range; the event ledger makes reruns idempotent."""
    if start >= end:
        raise typer.BadParameter("start must be earlier than end")
    processor = BatchProcessor()
    try:
        result = processor.process(records_between(archive, start, end))
    finally:
        processor.close()
    console.print(
        f"Backfill complete: accepted={result.accepted:,}, "
        f"duplicates={result.duplicates:,}, rejected={result.rejected:,}"
    )


if __name__ == "__main__":
    typer.run(main)
