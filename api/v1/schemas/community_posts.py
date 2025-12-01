from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class PostCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(...)
    photo_ids: Optional[List[UUID]] = Field(default=None, description="List of uploaded photo IDs to attach to post")


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    content: str
    views: int
    created_at: datetime
    photos: List["PostPhotoResponse"] = []


class PostPhotoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    post_id: UUID
    url: str


class CommentCreateRequest(BaseModel):
    comment: str