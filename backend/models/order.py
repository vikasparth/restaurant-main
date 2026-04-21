from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, EmailStr, Field, UUID4, model_validator, ConfigDict


class OrderItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    menu_item_id: str = Field(..., min_length=1)
    quantity: int = Field(..., ge=1)


class OrderCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    idempotency_key: UUID4
    customer_name: str = Field(..., min_length=1)
    customer_email: EmailStr
    customer_phone: str = Field(..., min_length=1)
    order_type: Literal["pickup", "delivery"]
    scheduled_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    scheduled_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    items: list[OrderItemRequest] = Field(..., min_length=1)
    delivery_address: str | None = None
    delivery_zip: str | None = None
    special_instructions: str | None = Field(None, max_length=500)

    @model_validator(mode="after")
    def delivery_fields_required(self) -> OrderCreateRequest:
        if self.order_type == "delivery":
            if not self.delivery_address:
                raise ValueError("delivery_address is required for delivery orders")
            if not self.delivery_zip:
                raise ValueError("delivery_zip is required for delivery orders")
        return self


class OrderCreateResponse(BaseModel):
    reference_number: str
    status: str
    order_type: str
    scheduled_date: str
    scheduled_time: str
    subtotal: float
    delivery_fee: float
    total: float
