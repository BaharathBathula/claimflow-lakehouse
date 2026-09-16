from __future__ import annotations

import json
import os
from collections.abc import Iterable
from typing import Any

from claimflow.ingest import BatchProcessor
from claimflow.models import EventEnvelope

TOPICS = {
    "policy": "claimflow.policy.events",
    "claim": "claimflow.claim.events",
    "payment": "claimflow.payment.events",
}


def _kafka_classes() -> tuple[Any, Any]:
    try:
        from confluent_kafka import Consumer, Producer
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise RuntimeError("Install Kafka support with: pip install -e '.[kafka]'") from exc
    return Consumer, Producer


def publish(events: Iterable[EventEnvelope], bootstrap_servers: str | None = None) -> int:
    _, producer_class = _kafka_classes()
    producer = producer_class(
        {
            "bootstrap.servers": bootstrap_servers
            or os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
            "enable.idempotence": True,
            "acks": "all",
            "compression.type": "zstd",
            "linger.ms": 20,
        }
    )
    count = 0
    for event in events:
        entity = event.event_type.split(".", maxsplit=1)[0]
        producer.produce(
            TOPICS[entity],
            key=event.correlation_id.encode(),
            value=json.dumps(event.model_dump(mode="json"), separators=(",", ":")).encode(),
        )
        producer.poll(0)
        count += 1
    producer.flush(30)
    return count


def consume_forever(
    processor: BatchProcessor,
    bootstrap_servers: str | None = None,
    max_messages: int = 0,
    batch_size: int = 500,
) -> None:
    consumer_class, _ = _kafka_classes()
    consumer = consumer_class(
        {
            "bootstrap.servers": bootstrap_servers
            or os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
            "group.id": "claimflow-bronze-writer-v1",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
    consumer.subscribe(list(TOPICS.values()))
    processed = 0
    try:
        while max_messages == 0 or processed < max_messages:
            messages = consumer.consume(num_messages=batch_size, timeout=2.0)
            valid = [message.value() for message in messages if message and not message.error()]
            if not valid:
                continue
            result = processor.process(valid)
            consumer.commit(asynchronous=False)
            processed += result.accepted + result.rejected + result.duplicates
    finally:
        consumer.close()
        processor.close()
