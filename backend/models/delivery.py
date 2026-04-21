from pydantic import BaseModel, field_validator, ConfigDict


class DeliveryValidateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    zip_code: str

    @field_validator("zip_code")
    @classmethod
    def zip_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("zip_code must not be empty")
        return v


class DeliveryValidateResponse(BaseModel):
    is_covered: bool
    city: str | None  # None means null — allowed when zip is not cvered
