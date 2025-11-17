from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
import uuid

class WaitlistCreate(BaseModel):
    full_name: str
    email: EmailStr
    source: str

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

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Source cannot be empty")
        return v.strip()


class WaitlistResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}