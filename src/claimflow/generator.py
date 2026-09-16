from __future__ import annotations

import json
import random
import uuid
from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from faker import Faker

from claimflow.models import (
    ClaimPayload,
    ClaimStatus,
    EventEnvelope,
    PaymentPayload,
    PolicyPayload,
    PolicyStatus,
)

NAMESPACE = uuid.UUID("a68af5a1-9bde-4930-a5ab-24a803b6d0bb")
STATES = ["CA", "TX", "FL", "NY", "IL", "GA", "NC", "OH"]
LINES = ["commercial_auto", "general_liability", "workers_comp", "property"]
CLAIM_TYPES = ["collision", "theft", "water_damage", "bodily_injury", "property_damage"]
SOURCES = ["portal", "mobile", "call_center", "partner_api"]


def _id(prefix: str, seed: int, index: int) -> str:
    return f"{prefix}-{uuid.uuid5(NAMESPACE, f'{seed}:{prefix}:{index}').hex[:12]}"


def _event(
    *, index: int, seed: int, event_type: str, correlation_id: str, payload: dict, at: datetime
) -> EventEnvelope:
    return EventEnvelope(
        event_id=_id("evt", seed, index),
        event_type=event_type,
        occurred_at=at,
        correlation_id=correlation_id,
        payload=payload,
    )


def generate_events(count: int = 5_000, seed: int = 42) -> Iterator[EventEnvelope]:
    """Generate deterministic, referentially consistent insurance events."""
    if count < 20:
        raise ValueError("count must be at least 20")

    rng = random.Random(seed)
    fake = Faker()
    Faker.seed(seed)
    base = datetime(2025, 1, 1, 8, tzinfo=UTC)
    policy_count = max(10, count // 5)
    claim_count = max(8, count * 2 // 5)
    index = 0
    policies: list[PolicyPayload] = []

    for i in range(policy_count):
        effective = date(2025, 1, 1) + timedelta(days=rng.randint(0, 240))
        policy = PolicyPayload(
            policy_id=_id("pol", seed, i),
            customer_id=_id("cus", seed, i),
            customer_name=fake.name(),
            customer_email=fake.email(),
            line_of_business=rng.choice(LINES),
            state=rng.choice(STATES),
            effective_date=effective,
            expiration_date=effective + timedelta(days=365),
            annual_premium=round(rng.uniform(1_200, 48_000), 2),
            coverage_limit=rng.choice([100_000, 250_000, 500_000, 1_000_000]),
            deductible=rng.choice([500, 1_000, 2_500, 5_000]),
            status="active",
        )
        policies.append(policy)
        yield _event(
            index=index,
            seed=seed,
            event_type="policy.created",
            correlation_id=policy.policy_id,
            payload=policy.model_dump(mode="json"),
            at=base + timedelta(minutes=index),
        )
        index += 1

    claims: list[ClaimPayload] = []
    for i in range(claim_count):
        policy = rng.choice(policies)
        loss = policy.effective_date + timedelta(days=rng.randint(1, 300))
        report_delay = rng.randint(0, 14)
        severity = rng.choices([1, 2, 3, 4, 5], weights=[30, 30, 22, 13, 5])[0]
        reserve = round(rng.uniform(800, 9_000) * severity, 2)
        claim = ClaimPayload(
            claim_id=_id("clm", seed, i),
            policy_id=policy.policy_id,
            claimant_name=fake.name(),
            claimant_email=fake.email(),
            loss_date=loss,
            reported_at=datetime.combine(
                loss + timedelta(days=report_delay), datetime.min.time(), tzinfo=UTC
            ),
            claim_type=rng.choice(CLAIM_TYPES),
            state=policy.state,
            reserve_amount=reserve,
            paid_amount=0,
            status="open",
            adjuster_id=f"adj-{rng.randint(1, 40):03d}",
            severity=severity,
            source_system=rng.choice(SOURCES),
        )
        claims.append(claim)
        yield _event(
            index=index,
            seed=seed,
            event_type="claim.opened",
            correlation_id=claim.claim_id,
            payload=claim.model_dump(mode="json"),
            at=base + timedelta(minutes=index),
        )
        index += 1

    while index < count:
        claim = rng.choice(claims)
        event_choice = rng.random()
        if event_choice < 0.08:
            policy = rng.choice(policies)
            new_status = rng.choices(
                [PolicyStatus.ACTIVE, PolicyStatus.CANCELLED, PolicyStatus.EXPIRED],
                weights=[80, 12, 8],
            )[0]
            updated_policy = policy.model_copy(
                update={
                    "status": new_status,
                    "annual_premium": round(policy.annual_premium * rng.uniform(0.96, 1.08), 2),
                }
            )
            policies[policies.index(policy)] = updated_policy
            yield _event(
                index=index,
                seed=seed,
                event_type="policy.updated",
                correlation_id=policy.policy_id,
                payload=updated_policy.model_dump(mode="json"),
                at=base + timedelta(minutes=index),
            )
        elif event_choice < 0.72:
            progress = rng.random()
            if progress < 0.20:
                status = "investigating"
                paid = claim.paid_amount
            elif progress < 0.72:
                status = "approved"
                paid = round(claim.reserve_amount * rng.uniform(0.2, 0.75), 2)
            elif progress < 0.91:
                status = "closed"
                paid = round(claim.reserve_amount * rng.uniform(0.55, 1.0), 2)
            else:
                status = "denied"
                paid = 0
            updated = claim.model_copy(update={"status": ClaimStatus(status), "paid_amount": paid})
            claims[claims.index(claim)] = updated
            yield _event(
                index=index,
                seed=seed,
                event_type="claim.updated",
                correlation_id=claim.claim_id,
                payload=updated.model_dump(mode="json"),
                at=base + timedelta(minutes=index),
            )
        else:
            amount = round(max(50, claim.reserve_amount * rng.uniform(0.03, 0.25)), 2)
            payment = PaymentPayload(
                payment_id=_id("pay", seed, index),
                claim_id=claim.claim_id,
                payment_date=claim.loss_date + timedelta(days=rng.randint(5, 90)),
                amount=amount,
                payment_type=rng.choice(["indemnity", "expense", "medical", "repair"]),
                payee_name=fake.name(),
                payment_status=rng.choices(["issued", "cleared", "void"], [25, 70, 5])[0],
            )
            yield _event(
                index=index,
                seed=seed,
                event_type="payment.issued",
                correlation_id=claim.claim_id,
                payload=payment.model_dump(mode="json"),
                at=base + timedelta(minutes=index),
            )
        index += 1


def write_ndjson(events: Iterator[EventEnvelope], output: Path, invalid_rate: float = 0) -> int:
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output.open("w", encoding="utf-8") as handle:
        for event in events:
            record = event.model_dump(mode="json")
            if (
                invalid_rate
                and not event.event_type.startswith("policy.")
                and count > 0
                and count % max(1, int(1 / invalid_rate)) == 0
            ):
                record["payload"].pop(next(iter(record["payload"])), None)
            handle.write(json.dumps(record, separators=(",", ":")) + "\n")
            count += 1
    return count
