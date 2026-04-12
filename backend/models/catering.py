from uuid import UUID
from pydantic import BaseModel, Field


class CateringItemRequest(BaseModel):
    item_id: str
    trays: int = Field(..., ge=1)


class CateringCreateRequest(BaseModel):
    idempotency_key: UUID
    customer_name: str
    customer_email: str
    customer_phone: str
    event_date: str        # "YYYY-MM-DD"
    event_time: str        # "HH:MM"
    delivery_address: str
    zip_code: str
    items: list[CateringItemRequest] = Field(..., min_length=1)
    special_instructions: str | None = None


class CateringCreateResponse(BaseModel):
    reference_number: str
    status: str
    total_amount: float
    deposit_amount: float
    event_date: str
    event_time: str
