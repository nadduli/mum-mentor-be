from pydantic import BaseModel, EmailStr, field_validator

class ForgotPassword(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Email field cannot be empty")
        return v.strip().lower()