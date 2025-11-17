from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
import uuid

class WaitlistCreate(BaseModel):
    full_name: str = Field(..., alias="name")
    email: EmailStr
    # source: str


    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Full name cannot be empty")
        return v.strip()

    # Normalize email
    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    # Allow population by either alias ("name") or internal field ("full_name")
    model_config = {
        "populate_by_name": True
    }


class WaitlistResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str
    # source: str
    created_at: datetime

    model_config = {"from_attributes": True}
