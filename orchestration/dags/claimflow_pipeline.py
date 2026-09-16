"""Airflow DAG for scheduled ClaimFlow lakehouse maintenance.

This file is intentionally self-contained so it can be copied into an existing
Airflow deployment. Set CLAIMFLOW_PROJECT_ROOT in the Airflow environment.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_ROOT = os.getenv("CLAIMFLOW_PROJECT_ROOT", "/opt/airflow/claimflow")
DBT = f"dbt --project-dir {PROJECT_ROOT}/transform --profiles-dir {PROJECT_ROOT}/transform"

with DAG(
    dag_id="claimflow_lakehouse",
    description="Transform, test, and publish insurance claims data products",
    start_date=datetime(2025, 1, 1),
    schedule="*/15 * * * *",
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "data-platform",
        "retries": 2,
        "retry_delay": timedelta(minutes=2),
        "execution_timeout": timedelta(minutes=20),
    },
    tags=["claimflow", "lakehouse", "insurance"],
) as dag:
    transform = BashOperator(
        task_id="build_silver_and_gold",
        bash_command=f"cd {PROJECT_ROOT} && {DBT} run",
    )
    dbt_quality = BashOperator(
        task_id="run_dbt_contract_tests",
        bash_command=f"cd {PROJECT_ROOT} && {DBT} test",
    )
    quality_slo = BashOperator(
        task_id="enforce_quality_slos",
        bash_command=f"cd {PROJECT_ROOT} && python -m claimflow.quality",
    )

    transform >> dbt_quality >> quality_slo

