from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class MilestoneBase(BaseModel):
    name: str
    description: Optional[str] = None
    category_id: uuid.UUID
    child_id: Optional[uuid.UUID] = None

class MilestoneCreate(MilestoneBase):
    pass

class MilestoneToggle(BaseModel):
    completed: bool
    child_id: Optional[uuid.UUID] = None

class MilestoneResponse(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    owner_type: str
    name: str
    description: Optional[str]
    status: str
    category_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True