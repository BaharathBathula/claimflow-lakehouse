from prometheus_client import Counter, Gauge, Histogram

EVENTS_ACCEPTED = Counter(
    "claimflow_events_accepted_total", "Valid events written to the Bronze layer", ["entity"]
)
EVENTS_REJECTED = Counter(
    "claimflow_events_rejected_total", "Events sent to the dead-letter queue", ["reason"]
)
EVENTS_DUPLICATE = Counter(
    "claimflow_events_duplicate_total", "Duplicate events skipped by the ingestion ledger"
)
INGEST_LATENCY = Histogram(
    "claimflow_ingest_batch_seconds", "Time required to validate and persist an ingestion batch"
)
LAST_EVENT_EPOCH = Gauge(
    "claimflow_last_event_epoch_seconds", "Event-time timestamp of the most recent accepted event"
)
