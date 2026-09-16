# LinkedIn Launch Post

## Paste-ready post

I built **ClaimFlow Lakehouse** — a production-style data engineering platform for real-time insurance claims.

The problem I wanted to solve was not simply moving data from A to B. Insurance events arrive from multiple systems, can be duplicated or malformed, and contain sensitive customer information. The platform needed to turn those events into reliable operational data without hiding failure cases.

What I implemented:

• Kafka-compatible streaming with Redpanda  
• Versioned contracts for policy, claim, and payment events  
• Idempotent, at-least-once ingestion with a dead-letter queue  
• HMAC-based PII tokenization before Bronze storage  
• Zstandard-compressed, partitioned Parquet lakehouse storage  
• dbt Silver and Gold models, including an SCD Type 2 policy dimension  
• Data-quality, relationship, uniqueness, and financial controls  
• Airflow orchestration and Prometheus/Grafana observability  
• FastAPI analytics endpoints and a Streamlit operations dashboard  
• GitHub Codespaces and CI so the project is reproducible without local setup

On the verified demo run, the pipeline processed **5,000 synthetic events**, quarantined **37 deliberately invalid records**, produced **1,993 current claims**, built **9 dbt models**, and passed **15 data tests**.

One design decision I would defend: I did not claim “exactly once.” ClaimFlow uses at-least-once delivery with deterministic event IDs, an ingestion ledger, and downstream deduplication. That is a more honest and operable failure model for this architecture.

The default demo uses DuckDB and local Parquet to keep it free and reproducible. The repository also documents how each component maps to AWS, Azure, or GCP for production scale.

GitHub: **[ADD YOUR REPOSITORY LINK]**

I would value feedback from data engineers on the ingestion and data-quality design.

#DataEngineering #ApacheKafka #dbt #DataQuality #Lakehouse #Python #InsuranceTechnology

## What to attach

1. `assets/claimflow-cover.png`
2. A screenshot of the Streamlit dashboard after running `make demo` and `make dashboard`
3. A screenshot of the successful dbt test summary showing `PASS=15`

Do not post until the GitHub repository link works publicly and its CI run is green.
