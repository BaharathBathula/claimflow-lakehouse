# Recruiter and Interview Guide

## 30-second explanation

“ClaimFlow is a production-style insurance claims lakehouse I built to demonstrate the full data lifecycle. Kafka-compatible events are validated against versioned contracts, sensitive fields are tokenized, valid records land in partitioned Parquet, and dbt builds tested Silver and Gold models. The platform exposes operational KPIs through FastAPI and Streamlit, includes Airflow orchestration and Prometheus/Grafana observability, and runs end to end in GitHub Codespaces.”

## What I personally designed

- Event envelope and entity contracts for policies, claims, and payments
- At-least-once ingestion strategy and dual deduplication controls
- PII tokenization boundary and dead-letter workflow
- Medallion data model, SCD Type 2 policy dimension, and claim-payment reconciliation
- dbt quality gates, bounded backfill utility, and incident runbook
- API, dashboard, container stack, Codespaces experience, and CI pipeline

## Questions to expect

### Why not promise exactly-once delivery?

End-to-end exactly-once requires transactional coordination across Kafka and the object-store commit. ClaimFlow chooses at-least-once delivery, deterministic event IDs, idempotent processing, and downstream deduplication. That is simpler to operate and protects against silent loss.

### How would you scale it?

Partition topics by stable business key, scale consumers up to the partition count, compact small Parquet files, move storage to an object store with Iceberg/Delta atomic commits, and run transformations on a distributed engine. Measure first: input rate, consumer lag, batch latency, file sizes, and query scan volume.

### How do you handle schema evolution?

The event envelope carries an `event_version`. Additive compatible fields can be accepted with contract updates; breaking changes require a new version and parallel parsing. CI should enforce compatibility through a schema registry before producer deployment.

### Is the risk score machine learning?

No. It is an explainable operational prioritization rule built from synthetic data. Presenting it as a validated fraud model would be misleading. A real model would require governed labels, bias analysis, offline/online validation, monitoring, and human oversight.

### What is the biggest limitation?

The reproducible demo runs on one machine. It proves contracts, correctness patterns, modeling, and operability—not distributed throughput. The cloud mapping documents the components that change for production scale.

## Resume bullets

- Built an event-driven insurance claims lakehouse using Kafka-compatible streaming, Parquet, dbt, DuckDB, Airflow, FastAPI, and Streamlit, with a fully reproducible Codespaces demo.
- Implemented versioned data contracts, HMAC-based PII tokenization, dead-letter quarantine, idempotent replay, and dual-layer event deduplication for reliable at-least-once processing.
- Modeled a Type 2 policy dimension and tested Gold operational data products with CI-enforced uniqueness, referential-integrity, accepted-value, financial, and quality-SLO checks.

