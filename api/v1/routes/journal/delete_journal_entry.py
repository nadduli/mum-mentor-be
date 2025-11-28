from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
import uuid

from api.db.database import get_db
from api.utils.deps import get_current_user
from api.v1.models.user.user import User
from api.v1.services.journal import JournalService
from api.utils.responses import success_response
from api.utils.logger import logger

router = APIRouter(prefix="/journal", tags=["Journal"])

@router.delete("/{entry_id}", status_code=status.HTTP_200_OK)
def delete_journal_entry(
    entry_id: uuid.UUID,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a specific journal entry.
    """
    logger.info(f"User {current_user.id} attempting to delete journal {entry_id}")
    JournalService.delete_journal(session, entry_id, current_user.id)
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Journal entry deleted successfully",
        data=None
    )
