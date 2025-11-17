# schemas/auth.py
from pydantic import BaseModel



class RefreshTokenRequest(BaseModel):
    refresh_token: str