from __future__ import annotations

import shutil
from pathlib import Path
from typing import Annotated

import typer
from prometheus_client import start_http_server
from rich.console import Console

from claimflow.generator import generate_events, write_ndjson
from claimflow.ingest import BatchProcessor, read_ndjson
from claimflow.kafka_io import consume_forever, publish

app = typer.Typer(help="ClaimFlow Lakehouse command line interface", no_args_is_help=True)
console = Console()


@app.command("generate")
def generate_command(
    events: Annotated[int, typer.Option(min=20)] = 5_000,
    output: Path = Path("data/inbox/events.ndjson"),
    seed: int = 42,
    invalid_rate: Annotated[float, typer.Option(min=0, max=0.2)] = 0.01,
) -> None:
    count = write_ndjson(generate_events(events, seed), output, invalid_rate)
    console.print(f"[green]Generated {count:,} events[/green] → {output}")


@app.command("ingest-file")
def ingest_file_command(
    path: Path, batch_size: Annotated[int, typer.Option(min=1)] = 1_000
) -> None:
    processor = BatchProcessor()
    total = {"accepted": 0, "rejected": 0, "duplicates": 0, "files": 0}
    batch: list[str] = []
    try:
        for line in read_ndjson(path):
            batch.append(line)
            if len(batch) >= batch_size:
                result = processor.process(batch)
                for key, value in zip(total, result.__dict__.values(), strict=True):
                    total[key] += value
                batch.clear()
        if batch:
            result = processor.process(batch)
            for key, value in zip(total, result.__dict__.values(), strict=True):
                total[key] += value
    finally:
        processor.close()
    console.print(
        "[green]Ingestion complete[/green] "
        f"accepted={total['accepted']:,} rejected={total['rejected']:,} "
        f"duplicates={total['duplicates']:,} parquet_files={total['files']:,}"
    )


@app.command("publish-kafka")
def publish_kafka_command(
    events: Annotated[int, typer.Option(min=20)] = 5_000,
    bootstrap_servers: str = "localhost:9092",
    seed: int = 42,
) -> None:
    count = publish(generate_events(events, seed), bootstrap_servers)
    console.print(f"[green]Published {count:,} events[/green]")


@app.command("ingest-kafka")
def ingest_kafka_command(
    bootstrap_servers: str = "localhost:9092",
    max_messages: Annotated[int, typer.Option(min=0)] = 0,
    metrics_port: Annotated[int, typer.Option(min=1, max=65535)] = 9_108,
) -> None:
    start_http_server(metrics_port)
    console.print(f"Listening for events; Prometheus metrics on :{metrics_port}/metrics")
    consume_forever(BatchProcessor(), bootstrap_servers, max_messages)


@app.command("reset")
def reset_command(
    yes: Annotated[bool, typer.Option("--yes", help="Confirm deletion of generated data")] = False,
) -> None:
    if not yes:
        raise typer.BadParameter("Pass --yes to remove generated project data")
    targets = [
        Path("data/inbox/events.ndjson"),
        Path("data/lake/bronze"),
        Path("data/dlq"),
        Path("data/warehouse"),
    ]
    for target in targets:
        if target.is_dir():
            shutil.rmtree(target)
            target.mkdir(parents=True, exist_ok=True)
        elif target.exists():
            target.unlink()
    console.print("[yellow]Generated ClaimFlow data removed[/yellow]")


if __name__ == "__main__":
    app()
