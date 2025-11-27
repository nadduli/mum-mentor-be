from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class PostCreateRequest(BaseModel):
    title: str = Field(..., max_length=200)
    content: str = Field(...)


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    content: str
    created_at: datetime
