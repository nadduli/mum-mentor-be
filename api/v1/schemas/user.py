import re
from datetime import datetime
from typing import Any, Final

from pydantic import BaseModel, EmailStr, Field, field_validator

PASSWORD_RULES: Final[tuple[tuple[re.Pattern[str], str], ...]] = (
    (re.compile(r".{8,}"), "Password must be at least 8 characters long"),
    (re.compile(r"[A-Z]"), "Password must contain at least one uppercase letter"),
    (re.compile(r"[a-z]"), "Password must contain at least one lowercase letter"),
    (re.compile(r"\d"), "Password must contain at least one digit"),
    (re.compile(r"[!@#$%^&*(),.?\":{}|<>]"), "Password must contain at least one special character"),
)

NAME_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[a-zA-Z\s\-']+$")


class UserRegistrationRequest(BaseModel):
    """Schema for user registration request"""
    full_name: str = Field(..., min_length=2, max_length=100, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, max_length=100, description="User's password")
    confirm_password: str = Field(..., min_length=8, max_length=100, description="Password confirmation")

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength"""
        for pattern, message in PASSWORD_RULES:
            if not pattern.search(v):
                raise ValueError(message)
        return v

    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v: str, info: Any) -> str:
        """Validate that passwords match"""
        password = info.data.get('password') if info.data else None
        if password and v != password:
            raise ValueError('Passwords do not match')
        return v

    @field_validator('full_name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name fields"""
        if not v.strip():
            raise ValueError('Name cannot be empty or only whitespace')
        if not NAME_PATTERN.match(v):
            raise ValueError('Name can only contain letters, spaces, hyphens, and apostrophes')
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "example": {
                "full_name": "Lex Lee",
                "email": "lex.lee@example.com",
                "password": "SecurePass123!",
                "confirm_password": "SecurePass123!"
            }
        }
    }


class UserRegistrationResponse(BaseModel):
    """Schema for user registration response"""
    id: str
    full_name: str
    email: str | None
    email_verified: bool
    phone_verified: bool
    role: str
    is_active: bool
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "full_name": "Lex Lee",
                "email": "lex.lee@example.com",
                "email_verified": False,
                "phone_verified": False,
                "role": "user",
                "is_active": True,
                "created_at": "2025-11-16T12:00:00"
            }
        }
    }
