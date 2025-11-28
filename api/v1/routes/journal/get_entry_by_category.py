from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.utils.deps import get_current_user
from api.utils.responses import success_response, fail_response
from api.v1.services.get_entry_by_category import get_entries_by_category
from api.v1.models.user.user import User

journal_entry_router = APIRouter(prefix="/journal", tags=["Journal"])

@journal_entry_router.get("/by-category")
async def get_journal_entry_by_category(
    category: str = Query(..., description="Category name to search for"),
    limit: int = Query(10, description="Number of entries to return", ge=1, le=100),
    offset: int = Query(0, description="Number of entries to skip", ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        filtered_journal_entries = get_entries_by_category(
            db=db,
            category_title=category,
            user_id=current_user.id,
            limit=limit,
            offset=offset
        )

        return success_response(
            status_code=200,
            message=f"Journal entries for category '{category}'",
            data=filtered_journal_entries
        )
    except Exception as e:
        return fail_response(
            status_code=500,
            message="Error retrieving journal entries",
            context=str(e)
        )
