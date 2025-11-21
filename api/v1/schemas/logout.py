from pydantic import BaseModel


class LogoutResponse(BaseModel):
    message: str
    success: bool


class LogoutAllResponse(BaseModel):
    message: str
    sessions_ended: int
    success: bool