from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.utils.deps import get_current_user
from api.utils.responses import success_response, fail_response
from api.v1.services.journal_service import JournalService
from api.v1.models.user.user import User

router = APIRouter(prefix="/journal", tags=["Journal"])

@router.get("/entries")
async def get_all_journal_entries(
    limit: int = Query(10, description="Number of entries to return", ge=1, le=100),
    offset: int = Query(0, description="Number of entries to skip", ge=0),
    sort_by: str = Query("entry_date", description="Field to sort by (entry_date or created_at)"),
    order: str = Query("desc", description="Sort order (asc or desc)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all journal entries for the authenticated user.
    
    Returns paginated journal entries with optional sorting.
    """
    try:
        result = JournalService.get_all_journals(
            db=db,
            user_id=str(current_user.id),
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            order=order
        )

        return success_response(
            status_code=200,
            message="Journal entries retrieved successfully",
            data={
                "entries": result["entries"],
                "total": result["total"],
                "limit": limit,
                "offset": offset
            }
        )
    except Exception as e:
        return fail_response(
            status_code=500,
            message="Error retrieving journal entries",
            context=str(e)
        )