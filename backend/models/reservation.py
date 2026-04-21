from __future__ import annotations
from pydantic import BaseModel, ConfigDict, EmailStr, Field, UUID4

class ReservationCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    idempotency_key: UUID4
    customer_name: str = Field(..., min_length=1)
    customer_email: EmailStr | None = None
    customer_phone: str = Field(..., min_length=1)
    party_size: int = Field(..., ge=1)
    reserved_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    reserved_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    notes: str | None = Field(None, max_length=500)


class ReservationCreateResponse(BaseModel):
    reference_number: str
    status: str
    party_size: int
    reserved_date: str
    reserved_time: str
