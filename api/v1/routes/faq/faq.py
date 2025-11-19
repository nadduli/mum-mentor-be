from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.db.database import get_db

from api.v1.services.faq.faq import FAQService
from api.v1.schemas.faq import FAQListResponse

router = APIRouter(prefix="/faqs", tags=["FAQ"])

@router.get("/", response_model=FAQListResponse)
def get_faqs(
    category: str | None = None,
    search: str | None = None,
    limit: int = 20,
    offset: int = 0,
    session: Session = Depends(get_db),
):
    faqs, total = FAQService.fetch_faqs(
        session=session,
        category=category,
        search=search,
        limit=limit,
        offset=offset,
    )

    return FAQListResponse(
        data=faqs,
        meta={
            "total": total,
            "limit": limit,
            "offset": offset,
        },
    )