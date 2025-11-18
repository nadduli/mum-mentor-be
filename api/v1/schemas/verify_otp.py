from pydantic import BaseModel, Field, field_validator
from typing import Literal

class VerifyOTPRequest(BaseModel):
    """Schema for OTP verification request"""
    #user_id: str = Field(..., description="User ID")
    otp_code: str = Field(..., min_length=4, max_length=10, description="OTP code")
    otp_type: Literal["email_verification", "phone_verification", "password_reset"] = Field(
        default="email_verification", 
        description="Type of OTP verification"
    )

    
    @field_validator("otp_code")
    @classmethod
    def validate_otp_code(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("otp_code cannot be empty")
        v = v.strip()
        if len(v) < 4 or len(v) > 10:
            raise ValueError("otp_code must be between 4 and 10 characters long")
        if not v.isdigit():
            raise ValueError("otp_code must contain only digits")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "otp_code": "123456",
                "otp_type": "password_reset", 
            }
        }
    }