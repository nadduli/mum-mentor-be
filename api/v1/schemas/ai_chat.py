"""
Pydantic schemas for AI Chat endpoints
"""

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class SendMessageRequest(BaseModel):
    """Request schema for sending a message"""
    message: str = Field(
        ..., 
        min_length=1, 
        max_length=5000,
        description="User message content"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "What should I expect in my first trimester?"
            }
        }
    }


class MessageResponse(BaseModel):
    """Schema for a single message"""
    id: UUID
    session_id: UUID
    sender: str  # "user" or "ai"
    message: str
    created_at: datetime
    
    model_config = {"from_attributes": True}


class ChatSessionResponse(BaseModel):
    """Schema for chat session details"""
    id: UUID
    user_id: UUID
    title: str | None
    created_at: datetime
    
    model_config = {"from_attributes": True}


class SendMessageResponse(BaseModel):
    """Response schema for send message endpoint (used in SSE events)"""
    type: str  # "start", "chunk", "done", "error"
    message_id: UUID | None = None
    content: str | None = None
    title: str | None = Field(None, description="Generated title for first message only")
    message: str | None = Field(None, description="Error message if type is 'error'")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {"type": "start", "message_id": "123e4567-e89b-12d3-a456-426614174000", "title": "Pregnancy Questions"},
                {"type": "chunk", "content": "Hello! "},
                {"type": "done", "message_id": "123e4567-e89b-12d3-a456-426614174001"},
                {"type": "error", "message": "An error occurred"}
            ]
        }
    }
