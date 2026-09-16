from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from claimflow.models import EventEnvelope, validate_payload


def test_contract_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        EventEnvelope.model_validate(
            {
                "event_id": "event-1234",
                "event_type": "claim.opened",
                "occurred_at": datetime.now(UTC),
                "correlation_id": "claim-1234",
                "payload": {},
                "unexpected": True,
            }
        )


def test_payload_contract_rejects_negative_financials() -> None:
    event = EventEnvelope.model_validate(
        {
            "event_id": "event-1234",
            "event_type": "payment.issued",
            "occurred_at": datetime.now(UTC),
            "correlation_id": "claim-1234",
            "payload": {
                "payment_id": "pay-1",
                "claim_id": "claim-1",
                "payment_date": "2025-01-03",
                "amount": -10,
                "payment_type": "repair",
                "payee_name": "Repair Shop",
                "payment_status": "issued",
            },
        }
    )
    with pytest.raises(ValidationError):
        validate_payload(event)
