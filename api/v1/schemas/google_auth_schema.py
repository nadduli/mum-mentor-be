# api/v1/schemas/google_auth_schema.py
from pydantic import BaseModel, Field
from typing import Optional


class GoogleAuthRequest(BaseModel):
    """
    Request payload from client containing the Google id_token.
    device_id and device_name are optional metadata fields.
    """
    id_token: str = Field(..., description="Google ID token (JWT) from client")
    device_id: Optional[str] = Field(None, description="Optional device id")
    device_name: Optional[str] = Field(None, description="Optional device name")


class GoogleAuthResponse(BaseModel):
    """
    Response returned after successful Google login.
    NOTE: refresh_token is intentionally omitted (we don't store refresh tokens).
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str


class GoogleVerificationResponse(BaseModel):
    google_id: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    picture: Optional[str] = None
    email_verified: bool = False


class UserResponse(BaseModel):
    id: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool
    email_verified: bool
    google_id: Optional[str] = None
    role: Optional[str] = None

class RevokeRequest(BaseModel):
    refresh_token: str
