from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
import math

from api.db.database import get_db
from api.v1.services.resource import ResourceService
from api.v1.schemas.resource import PaginatedResourceResponse

router = APIRouter(prefix="/resources", tags=["Resources"])

@router.get("/", status_code=status.HTTP_200_OK, response_model=PaginatedResourceResponse)
def get_all_resources(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    session: Session = Depends(get_db)
):
    """
    Get all resources (videos, articles) with pagination.
    Includes media and category details.
    """
    resources, total = ResourceService.get_all_resources(session, page, limit)
    
    total_pages = math.ceil(total / limit) if limit > 0 else 0

    return {
        "status": "success",
        "message": "Resources retrieved successfully",
        "data": resources, 
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }