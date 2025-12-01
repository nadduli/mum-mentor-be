from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict



class PostCreateRequest(BaseModel):
    title: str = Field(...,min_length=1, max_length=200)
    content: str = Field(...)


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    content: str
    views: int
    created_at: datetime

class CommentCreateRequest(BaseModel):
    comment: str
