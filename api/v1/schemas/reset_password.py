from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
import uuid

class ResetPassword(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str

    @field_validator("old_password")
    @classmethod
    def validate_old_password(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Old password field cannot be empty")
        if len(v.strip()) < 8:
            raise ValueError("Old password must be at least 8 characters long")
        return v.strip()

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("New password field cannot be empty")
        if len(v.strip()) < 8:
            raise ValueError("New password must be at least 8 characters long")
        return v.strip()

    @field_validator("confirm_password")
    @classmethod
    def validate_confirm_password(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Confirm password field cannot be empty")
        if len(v.strip()) < 8:
            raise ValueError("Confirm password must be at least 8 characters long")
        return v.strip()
