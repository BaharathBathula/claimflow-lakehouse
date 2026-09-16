from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import typer
from rich.console import Console
from rich.table import Table

console = Console()
DEFAULT_DB_PATH = Path(os.getenv("CLAIMFLOW_DB_PATH", "data/warehouse/claimflow.duckdb"))


def run_checks(
    db_path: Path = DEFAULT_DB_PATH,
    dlq_path: Path = Path("data/dlq/invalid-events.ndjson"),
    source_path: Path = Path("data/inbox/events.ndjson"),
    max_rejection_rate: float = 0.02,
) -> dict[str, object]:
    source_count = sum(1 for _ in source_path.open()) if source_path.exists() else 0
    rejected_count = sum(1 for _ in dlq_path.open()) if dlq_path.exists() else 0
    rejection_rate = rejected_count / source_count if source_count else 0

    connection = duckdb.connect(str(db_path), read_only=True)
    try:
        total_claims, orphan_claims, duplicate_claims, max_event_time = connection.execute(
            """
            select
              (select count(*) from silver.fct_claims_current),
              (select count(*) from silver.fct_claims_current where line_of_business is null),
              (select count(*) - count(distinct claim_id) from silver.fct_claims_current),
              (select max(occurred_at) from silver.fct_claims_current)
            """
        ).fetchone()
    finally:
        connection.close()

    checks = {
        "claims_present": total_claims > 0,
        "referential_integrity": orphan_claims == 0,
        "claim_uniqueness": duplicate_claims == 0,
        "rejection_rate_within_slo": rejection_rate <= max_rejection_rate,
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checked_at": datetime.now(UTC).isoformat(),
        "checks": checks,
        "metrics": {
            "source_events": source_count,
            "rejected_events": rejected_count,
            "rejection_rate": round(rejection_rate, 4),
            "total_claims": total_claims,
            "max_event_time": str(max_event_time),
        },
    }


def main(output: Path = Path("data/warehouse/quality-report.json")) -> None:
    report = run_checks()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    table = Table(title="ClaimFlow Data Quality SLOs")
    table.add_column("Check")
    table.add_column("Result")
    for check, passed in report["checks"].items():
        table.add_row(check, "PASS" if passed else "FAIL")
    console.print(table)
    if report["status"] != "pass":
        raise typer.Exit(1)


if __name__ == "__main__":
    typer.run(main)
