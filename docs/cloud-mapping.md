# Cloud Deployment Mapping

The open-source demo keeps the data contracts and transformation logic independent of a specific provider.

| Project component | AWS | Azure | GCP |
|---|---|---|---|
| Redpanda/Kafka | MSK Serverless | Event Hubs Kafka endpoint | Managed Service for Apache Kafka |
| Parquet lake | S3 | ADLS Gen2 | Cloud Storage |
| Catalog/table format | Glue + Iceberg | Unity Catalog/Delta | BigLake/Iceberg |
| Transform compute | EMR Serverless or Athena | Databricks or Fabric | Dataproc Serverless or BigQuery |
| Orchestration | MWAA | Data Factory/Managed Airflow | Cloud Composer |
| API | ECS Fargate/Lambda | Container Apps/Functions | Cloud Run |
| Metrics | Managed Prometheus/Grafana | Azure Monitor | Managed Prometheus |
| Secrets | Secrets Manager + KMS | Key Vault | Secret Manager + Cloud KMS |

## Production hardening backlog

1. Add Schema Registry compatibility checks in CI.
2. Store Bronze in Iceberg or Delta tables with atomic commits.
3. Replace the SQLite ledger with a transactional checkpoint store.
4. Add infrastructure as code, private networking, workload identity, and KMS keys.
5. Define retention, legal-hold, deletion, and field-level access policies.
6. Add OpenLineage metadata and alert routing to the incident platform.
7. Run load, recovery-point, and recovery-time tests against explicit SLOs.

