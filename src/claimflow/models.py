from __future__ import annotations

from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ClaimStatus(StrEnum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    APPROVED = "approved"
    DENIED = "denied"
    CLOSED = "closed"


class PolicyStatus(StrEnum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class EventEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=8)
    event_type: str = Field(pattern=r"^(policy|claim|payment)\.[a-z_]+$")
    event_version: int = Field(default=1, ge=1)
    occurred_at: datetime
    producer: str = "claimflow-simulator"
    correlation_id: str = Field(min_length=8)
    payload: dict[str, Any]

    @field_validator("occurred_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware")
        return value.astimezone(UTC)


class PolicyPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_id: str
    customer_id: str
    customer_name: str
    customer_email: str
    line_of_business: str
    state: str = Field(min_length=2, max_length=2)
    effective_date: date
    expiration_date: date
    annual_premium: float = Field(gt=0)
    coverage_limit: float = Field(gt=0)
    deductible: float = Field(ge=0)
    status: PolicyStatus

    @field_validator("customer_email")
    @classmethod
    def plausible_email(cls, value: str) -> str:
        if "@" not in value:
            raise ValueError("customer_email is invalid")
        return value.lower()


class ClaimPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: str
    policy_id: str
    claimant_name: str
    claimant_email: str
    loss_date: date
    reported_at: datetime
    claim_type: str
    state: str = Field(min_length=2, max_length=2)
    reserve_amount: float = Field(ge=0)
    paid_amount: float = Field(ge=0)
    status: ClaimStatus
    adjuster_id: str
    severity: int = Field(ge=1, le=5)
    source_system: str

    @field_validator("claimant_email")
    @classmethod
    def plausible_email(cls, value: str) -> str:
        if "@" not in value:
            raise ValueError("claimant_email is invalid")
        return value.lower()


class PaymentPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payment_id: str
    claim_id: str
    payment_date: date
    amount: float = Field(gt=0)
    payment_type: str
    payee_name: str
    payment_status: str


PAYLOAD_MODELS: dict[str, type[BaseModel]] = {
    "policy": PolicyPayload,
    "claim": ClaimPayload,
    "payment": PaymentPayload,
}


def validate_payload(event: EventEnvelope) -> BaseModel:
    entity = event.event_type.split(".", maxsplit=1)[0]
    model = PAYLOAD_MODELS.get(entity)
    if model is None:
        raise ValueError(f"unsupported event entity: {entity}")
    return model.model_validate(event.payload)
