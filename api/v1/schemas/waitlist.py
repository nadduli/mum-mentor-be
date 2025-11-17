from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
import uuid

class WaitlistCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Full name cannot be empty")
        return v.strip()

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class WaitlistResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str
    joined_at: datetime

    model_config = {"from_attributes": True}