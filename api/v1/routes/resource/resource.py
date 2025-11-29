from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
import math

from api.db.database import get_db
from api.utils.responses import fail_response, success_response
from api.v1.services.resource import ResourceService
from api.v1.schemas.resource import PaginatedResourceResponse, ResourceResponse

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


@router.get("/search", status_code=status.HTTP_200_OK)
def search_resources(
    title: str = Query(..., min_length=1, description="Search title"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    session: Session = Depends(get_db),
):
    """
    Search resources by title substring (case-insensitive).
    """

    try:
        resources, total = ResourceService.search_by_title(
            session=session,
            title=title,
            page=page,
            limit=limit
        )

        if not resources:
            return fail_response(
                status_code=404,
                message="No resources found",
                context={"title": title}
            )

        data = [ResourceResponse.model_validate(r) for r in resources]
        total_pages = (total + limit - 1) // limit

        payload = {
            "status": "success",
            "message": "Resources retrieved successfully",
            "data": data,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages
        }

        # 🔥 Wrap inside your project-wide success response format
        return success_response(
            status_code=200,
            message="Resources retrieved successfully",
            data=payload
        )

    except Exception as e:
        return fail_response(
            status_code=500,
            message="Failed to search resources",
            context={"error": str(e)}
        )