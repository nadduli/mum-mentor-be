from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.deps import get_current_user
from api.v1.models.user.user import User
from api.v1.schemas.journal import JournalCreateRequest, JournalCreateResponse
from api.v1.services.journal_service import JournalService
from api.utils.responses import success_response
from api.utils.logger import logger

router = APIRouter(
    prefix="/journal",
    tags=["Journal"]
)

@router.post("/entry/", response_model=None)
def create_journal(
    journal_data: JournalCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new journal entry.
    
    This endpoint allows an authenticated user to create a new journal entry.
    """
    logger.info(f"Creating journal for user_id={current_user.id}")
    
    journal = JournalService.create_journal(db, journal_data, str(current_user.id))
    
    if not journal:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create journal entry"
        )
        
    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Journal created successfully",
        data=JournalCreateResponse(
            journal_entry_id=journal.id,
            title=journal.title
        ).model_dump()
    )
