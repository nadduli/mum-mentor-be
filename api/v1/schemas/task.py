"""
Pydantic schemas for task-related operations and data models.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class TaskStatusUpdate(BaseModel):
    """Schema for updating the completion status of a task."""
    completed: bool


class EditTaskRequest(BaseModel):
    """Schema for editing a task"""

    name: Optional[str] = Field(None, max_length=200, description="Task name")
    description: Optional[str] = Field(
        None, max_length=1000, description="Task description"
    )
    due_date: Optional[str] = Field(None, description="Due date in ISO format")
    status: Optional[str] = Field(None, description="Task status (pending, completed, abandoned)")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate that the task name is not empty."""
        if v is not None and v.strip() == "":
            raise ValueError("Task name cannot be empty")
        return v
    
    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        """Validate that the task status is one of the allowed values."""
        if v is not None and v not in ["pending", "completed", "abandoned"]:
            raise ValueError("Status must be 'pending', 'completed', or 'abandoned'")
        return v


class Task(BaseModel):
    """Base schema for a task model."""
    id: UUID
    name: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: str
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskResponse(BaseModel):
    """Schema for task response"""

    id: UUID
    name: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: str
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
