# Architecture Decisions

## 1. Reproducibility before cloud complexity

**Decision:** use DuckDB and local partitioned Parquet in the default path.

**Why:** a recruiter can run the entire system in one Codespace without an account, credit card, or long-lived infrastructure. The interfaces remain cloud-portable.

**Trade-off:** this demo does not prove horizontal object-store throughput. A production deployment would replace the filesystem path with S3/ADLS and use a distributed query engine.

## 2. At-least-once ingestion with deterministic deduplication

**Decision:** commit Kafka offsets only after the Parquet batch is written and use both an ingestion ledger and downstream `event_id` deduplication.

**Why:** committing first can lose events; writing first can duplicate a batch after a crash. The chosen design prefers replayable duplicates over silent loss and removes duplicates in two layers.

## 3. HMAC tokens instead of raw PII

**Decision:** replace names and email addresses with keyed HMAC-SHA256 tokens before Bronze storage.

**Why:** deterministic tokens preserve analytical joins without storing clear-text PII. A plain hash would be vulnerable to dictionary attacks.

**Trade-off:** key rotation requires a controlled retokenization workflow. Production keys belong in a secrets manager or KMS-backed tokenization service.

## 4. Contracts at the ingestion boundary

**Decision:** validate the envelope and entity payload before persistence.

**Why:** invalid records are isolated early, while the original payload and failure reason remain available in the dead-letter queue.

## 5. Explainable operational risk score

**Decision:** use a transparent rule-based score for the work queue.

**Why:** the project is a data platform, not a claim-denial model. Explainable features demonstrate feature engineering without pretending that synthetic data validates a production ML model.

## 6. Airflow is optional in the default demo

**Decision:** ship an Airflow-ready DAG but do not start the full Airflow control plane for a five-minute demo.

**Why:** the DAG demonstrates scheduling, retries, timeouts, and quality gates; omitting several Airflow containers keeps the demo reliable on small Codespaces.

