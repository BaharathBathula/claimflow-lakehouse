# ClaimFlow Production Runbook

## Consumer lag is increasing

1. Confirm broker health and partition leadership.
2. Compare input rate with `claimflow_events_accepted_total` throughput.
3. Inspect p95 batch latency and storage write errors.
4. Scale consumer replicas only up to the topic partition count.
5. If the sink is degraded, pause producers where possible; do not commit offsets manually.
6. After recovery, verify lag returns to baseline and run the quality report.

## Rejection rate exceeds 2%

1. Stop automated promotion of Gold models.
2. Group DLQ records by validation reason and producer.
3. Compare `event_version` with the supported contract.
4. Coordinate a producer fix or deploy a backward-compatible parser.
5. Replay the affected event-time range and confirm the event ledger handles duplicates.

## Gold metrics are stale

1. Check the Airflow DAG state and the first failed task.
2. Verify Bronze file freshness and available disk/object-store capacity.
3. Run `dbt run --select +claims_kpis` followed by `dbt test` in a controlled shell.
4. Never bypass failed relationship or financial-value tests merely to refresh a dashboard.
5. Record the stale-data interval and downstream consumers affected.

## Suspected PII exposure

1. Treat the event as a security incident and restrict access to the affected storage path.
2. Identify the producer, fields, partitions, and time window.
3. Rotate the tokenization key only through the approved key-rotation process.
4. Reprocess affected data from the authorized source and invalidate cached outputs.
5. Preserve audit evidence and follow the organization's notification policy.

