from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from api.v1.services.milestone_service import MilestoneService
from api.v1.schemas.milestones import (
    ListMilestonesResponse,
    MilestoneSummaryResponse
)
from api.v1.dependencies.auth import get_current_user
from api.utils.deps import get_db
from api.utils.responses import (
    success_response,
)

router = APIRouter(prefix="/milestones", tags=["Milestones"])

@router.get(
    "/categories/{category_id}",
    response_model=ListMilestonesResponse,
    status_code=status.HTTP_200_OK,
)
def get_milestones_by_category(
    category_id: UUID,
    milestone_status: str = Query(..., enum=["pending", "completed"]),
    child_id: Optional[UUID] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get milestones for a specific category.
    """
    data = MilestoneService.get_milestones_by_category(
        db=db,
        category_id=category_id,
        user_id=current_user.id,
        milestone_status=milestone_status,
        child_id=child_id,
        page=page,
        limit=limit,
    )
    return success_response(
        message="Milestones fetched successfully",
        status_code=200,
        data=data
    )


@router.get(
    "/summary",
    response_model=MilestoneSummaryResponse,
    status_code=status.HTTP_200_OK,
)
def get_milestone_summary(
    child_id: Optional[UUID] = None,
    duration: str = Query("week", enum=["day", "week", "month", "year"]),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get a summary of milestones.
    """
    summary_data = MilestoneService.get_milestone_summary(
        db=db,
        user_id=current_user.id,
        child_id=child_id,
        duration=duration,
    )
    return success_response(
        message="Milestone summary fetched successfully",
        status_code=200,
        data=summary_data,
    )
