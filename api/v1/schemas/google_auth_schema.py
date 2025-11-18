from pydantic import BaseModel


class GoogleAuthRequest(BaseModel):
    id_token: str
    device_id: str | None = None
    device_name: str | None = None


class GoogleAuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str

class RevokeRequest(BaseModel):
    refresh_token: str