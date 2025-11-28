from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
import uuid

from api.db.database import get_db
from api.utils.deps import get_current_user
from api.v1.models.user.user import User
from api.v1.schemas.journal import JournalEdit, JournalResponse, JournalData
from api.v1.services.journal import JournalService
from api.utils.responses import success_response

router = APIRouter(prefix="/journal", tags=["Journal"])

@router.patch("/{entry_id}", status_code=status.HTTP_200_OK, response_model=JournalResponse)
def edit_journal_entry(
    entry_id: uuid.UUID,
    payload: JournalEdit,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Edit a specific journal entry.
    """
    updated_journal = JournalService.update_journal(session, entry_id, current_user.id, payload)

    response_data = JournalData.model_validate(updated_journal).model_dump()

    return success_response(
        status_code=status.HTTP_200_OK,
        message="Successfully edited entry",
        data=response_data
    )