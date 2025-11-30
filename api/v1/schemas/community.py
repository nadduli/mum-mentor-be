from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

class PostPhotoDTO(BaseModel):
    id: uuid.UUID
    url: str

    class Config:
        from_attributes = True

class PostResponse(BaseModel):
    id: uuid.UUID
    title: str
    content: str
    created_at: datetime
    views: int
    photos: List[PostPhotoDTO] = []
    likes_count: int = 0
    comments_count: int = 0
    
    class Config:
        from_attributes = True

class PostResponseWrapper(BaseModel):
    status: str
    message: str
    data: PostResponse

class LikeToggleResponse(BaseModel):
    """Response after toggling a like"""
    is_liked: bool
    likes_count: int

class LikeResponseWrapper(BaseModel):
    status: str
    message: str
    data: LikeToggleResponse