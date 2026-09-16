from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import duckdb
import typer
from rich.console import Console
from rich.table import Table

from claimflow.generator import generate_events, write_ndjson
from claimflow.ingest import BatchProcessor, read_ndjson

ROOT = Path(__file__).resolve().parents[2]
console = Console()


def _reset_demo_data() -> None:
    for relative in ["data/inbox", "data/lake/bronze", "data/dlq", "data/warehouse"]:
        target = ROOT / relative
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True, exist_ok=True)


def _run_dbt() -> None:
    env = os.environ.copy()
    env["CLAIMFLOW_DB_PATH"] = str(ROOT / "data/warehouse/claimflow.duckdb")
    env["CLAIMFLOW_BRONZE_PATH"] = str(ROOT / "data/lake/bronze")
    command = [
        sys.executable,
        str(ROOT / "scripts/run_dbt_cli.py"),
    ]
    options = [
        "--project-dir",
        str(ROOT / "transform"),
        "--profiles-dir",
        str(ROOT / "transform"),
    ]
    subprocess.run([*command, "run", *options], check=True, env=env)
    subprocess.run([*command, "test", *options], check=True, env=env)


def _summary() -> None:
    connection = duckdb.connect(str(ROOT / "data/warehouse/claimflow.duckdb"), read_only=True)
    row = connection.execute(
        "SELECT total_claims, open_claims, total_incurred, high_risk_claims, data_as_of "
        "FROM gold.claims_kpis"
    ).fetchone()
    table = Table(title="ClaimFlow Lakehouse — Demo Results")
    for column in ["Claims", "Open", "Total incurred", "High risk", "Data as of"]:
        table.add_column(column)
    table.add_row(f"{row[0]:,}", f"{row[1]:,}", f"${row[2]:,.0f}", f"{row[3]:,}", str(row[4]))
    console.print(table)
    connection.close()


def main(events: int = typer.Option(5_000, min=20), seed: int = 42) -> None:
    """Run a deterministic end-to-end portfolio demo without external services."""
    _reset_demo_data()
    inbox = ROOT / "data/inbox/events.ndjson"
    generated = write_ndjson(generate_events(events, seed), inbox, invalid_rate=0.01)
    console.print(f"1/3 Generated [bold]{generated:,}[/bold] source events")

    processor = BatchProcessor(
        ROOT / "data/lake/bronze",
        ROOT / "data/lake/bronze/_state/ledger.sqlite",
        ROOT / "data/dlq/invalid-events.ndjson",
    )
    result = processor.process(read_ndjson(inbox))
    processor.close()
    console.print(
        f"2/3 Bronze ingestion: [green]{result.accepted:,} accepted[/green], "
        f"[yellow]{result.rejected:,} quarantined[/yellow]"
    )
    _run_dbt()
    console.print("3/3 dbt models and data-quality tests passed")
    _summary()
    console.print("\nLaunch the dashboard with: [bold]make dashboard[/bold]")


if __name__ == "__main__":
    typer.run(main)
