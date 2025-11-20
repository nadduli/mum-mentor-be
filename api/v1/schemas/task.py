from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

class CreateTaskRequest(BaseModel):
    name: str
    description: Optional[str] = None
    due_date: datetime


class EditTaskRequest(BaseModel):
    """Schema for editing a task"""
    name: Optional[str] = Field(None, max_length=200, description="Task name")
    description: Optional[str] = Field(None, max_length=1000, description="Task description")
    due_date: Optional[datetime] = Field(None, description="Due date in ISO format")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError("Task name cannot be empty")
        return v


class TaskResponse(BaseModel):
    """Schema for task response"""
    id: str
    name: str
    description: Optional[str]
    due_date: Optional[str]
    status: str
    completed_at: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
