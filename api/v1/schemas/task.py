from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CreateTaskRequest(BaseModel):
    name: str
    description: Optional[str] = None
    due_date: datetime