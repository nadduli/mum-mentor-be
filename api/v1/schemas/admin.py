from typing import Optional
from pydantic import BaseModel, EmailStr, Field, SecretStr, ConfigDict


class AdminCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "full_name": "Jane Doe",
                "email": "jane@example.com",
                "phone": "+2348123456789",
                "password": "Str0ngP@ssw0rd",
                "role": "admin"
            }
        }
    )

    full_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, min_length=6, max_length=20)
    # Use SecretStr to avoid accidental logging/exposure of plaintext passwords
    password: SecretStr = Field(..., min_length=8, max_length=128, repr=False)
    role: str = "admin"  # default to "admin"


class AdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: str
    is_active: bool