import re
from pydantic import BaseModel, Field, field_validator

class AccountDeletionRequest(BaseModel):
    """Schema for account deletion request"""
    password: str = Field(..., min_length=1, description="User password for confirmation")
    confirmation_phrase: str = Field(..., description="Must type 'DELETE MY ACCOUNT' to confirm")

    @field_validator('confirmation_phrase')
    @classmethod
    def validate_confirmation_phrase(cls, v: str) -> str:
        """Validate confirmation phrase"""
        if v.strip().upper() != "DELETE MY ACCOUNT":
            raise ValueError('Must type "DELETE MY ACCOUNT" to confirm deletion')
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "example": {
                "password": "UserCurrentPassword123!",
                "confirmation_phrase": "DELETE MY ACCOUNT"
            }
        }
    }


class AccountDeletionResponse(BaseModel):
    """Schema for account deletion response"""
    message: str
    deletion_time: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Account and all associated data have been permanently deleted",
                "deletion_time": "2025-11-18T21:30:45Z"
            }
        }
    }