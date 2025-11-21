from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional


class TaskItem(BaseModel):
    name: str
    description: Optional[str] = None
    due_date: datetime
    status: str = "pending"
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class Pagination(BaseModel):
    page: int
    per_page: int
    total_count: int
    next: Optional[int] = None
    prev: Optional[int] = None


class TaskListData(BaseModel):
    details: List[TaskItem]
    pagination: Pagination


class TaskListResponse(BaseModel):
    status: str
    status_code: int
    message: str
    data: TaskListData