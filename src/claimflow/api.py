from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import duckdb
from fastapi import FastAPI, HTTPException, Query

DB_PATH = Path(os.getenv("CLAIMFLOW_DB_PATH", "data/warehouse/claimflow.duckdb"))


def _query(sql: str, parameters: list[Any] | None = None) -> list[dict[str, Any]]:
    if not DB_PATH.exists():
        raise HTTPException(status_code=503, detail="Warehouse not built. Run `make demo` first.")
    connection = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        cursor = connection.execute(sql, parameters or [])
        columns = [item[0] for item in cursor.description]
        return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
    finally:
        connection.close()


def create_app() -> FastAPI:
    application = FastAPI(
        title="ClaimFlow Analytics API",
        description="Read-only serving layer for curated insurance claims metrics.",
        version="1.0.0",
    )

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "healthy" if DB_PATH.exists() else "warehouse_unavailable"}

    @application.get("/v1/kpis")
    def kpis() -> dict[str, Any]:
        return _query("select * from gold.claims_kpis")[0]

    @application.get("/v1/claims/high-risk")
    def high_risk(limit: int = Query(25, ge=1, le=500)) -> list[dict[str, Any]]:
        return _query("select * from gold.high_risk_claims limit ?", [limit])

    @application.get("/v1/metrics/daily")
    def daily_metrics(
        state: str | None = Query(None, min_length=2, max_length=2),
        line_of_business: str | None = None,
        limit: int = Query(250, ge=1, le=5_000),
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        parameters: list[Any] = []
        if state:
            clauses.append("state = ?")
            parameters.append(state.upper())
        if line_of_business:
            clauses.append("line_of_business = ?")
            parameters.append(line_of_business)
        where = f"where {' and '.join(clauses)}" if clauses else ""
        parameters.append(limit)
        return _query(
            f"select * from gold.daily_claim_metrics {where} order by loss_date desc limit ?",
            parameters,
        )

    return application


app = create_app()
