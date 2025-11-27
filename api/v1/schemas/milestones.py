from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class Milestone(BaseModel):
    id: UUID
    owner_id: UUID
    owner_type: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MilestoneCategoryStats(BaseModel):
    pending_milestones: int
    completed_milestones: int


class MilestoneCategory(BaseModel):
    id: UUID
    owner_id: UUID
    owner_type: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    stats: MilestoneCategoryStats

    class Config:
        from_attributes = True


class Pagination(BaseModel):
    next_cursor: Optional[str] = None
    prev_cursor: Optional[str] = None
    per_page: int


class ListMilestonesData(BaseModel):
    category: MilestoneCategory
    milestones: List[Milestone]
    pagination: Pagination


class ListMilestonesResponse(BaseModel):
    message: str
    success: bool
    data: ListMilestonesData


class MilestoneSummary(BaseModel):
    completed_milestones: int
    created_milestones: int


class MilestoneSummaryResponse(BaseModel):
    message: str
    success: bool
    data: MilestoneSummary
