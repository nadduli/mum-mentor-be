from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from api.db.database import get_db
from api.utils.deps import get_current_user
from api.utils.responses import success_response
from api.v1.schemas.milestone import MilestoneCreate, MilestoneResponse, MilestoneToggle
from api.v1.services.milestone import MilestoneService

router = APIRouter(prefix="/milestones", tags=["Milestones"])

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_milestone(
    payload: MilestoneCreate,
    session: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new milestone for Mother or Child."""
    milestone = MilestoneService.create(session, current_user.id, payload)
    
    response_data = MilestoneResponse.model_validate(milestone).model_dump()

    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Milestone created successfully",
        data=response_data
    )

@router.patch("/{milestone_id}/status", status_code=status.HTTP_201_CREATED)
def toggle_milestone_status(
    milestone_id: uuid.UUID,
    payload: MilestoneToggle,
    session: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Toggle status between pending and completed."""
    milestone = MilestoneService.toggle_status(session, current_user.id, milestone_id, payload)

    response_data = MilestoneResponse.model_validate(milestone).model_dump()

    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Milestone status updated successfully",
        data=response_data
    )

@router.get("/pending", status_code=status.HTTP_200_OK)
def get_pending_milestones(
    child_id: Optional[uuid.UUID] = Query(None),
    session: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all pending milestones."""
    milestones = MilestoneService.get_pending(session, current_user.id, child_id)
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Pending milestones retrieved successfully",
        data={
            "details": [
                MilestoneResponse.model_validate(m).model_dump() 
                for m in milestones
            ]
        }
    )