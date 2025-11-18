from pydantic import BaseModel, field_validator


class VerifyOTP(BaseModel):
    user_id: str
    otp_code: str
    otp_type: str = "email_verification"

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("user_id cannot be empty")
        return v.strip()

    @field_validator("otp_code")
    @classmethod
    def validate_otp_code(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("otp_code cannot be empty")
        v = v.strip()
        if len(v) < 4 or len(v) > 10:
            raise ValueError("otp_code must be between 4 and 10 characters long")
        return v
