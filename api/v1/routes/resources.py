from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
import math

from api.db.database import get_db
from api.v1.services.resource import ResourceService
from api.v1.schemas.resource import PaginatedResourceResponse, ResourceCreate, CategoryCreate
from fastapi import HTTPException
from api.utils.deps import get_current_user
from api.utils.logger import logger
from api.v1.models.user.user import User
from api.utils.responses import success_response, fail_response

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


@router.post("/categories", status_code=status.HTTP_201_CREATED)
def create_category(
    schema: CategoryCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new category for resources."""
    try:
        category = ResourceService.create_category(session, schema)
        return success_response(
            message="Category created successfully",
            status_code=201,
            data={"id": category.id, "name": category.name}
        )
    except HTTPException as e:
        logger.error(f"HTTP error creating resource {e.status_code}: {str(e)}", exc_info=True)
        return fail_response(message="Invalid Request", status_code=e.status_code)
    except Exception as e:
        logger.error(f"Error creating category: {str(e)}", exc_info=True)
        return fail_response(message="Failed to create category", status_code=500)


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_resource(
    schema: ResourceCreate,
    session: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new resource (article/video content)."""
    try:
        resource = ResourceService.create_resource(session, schema)
        return success_response(
            message="Resource created successfully",
            status_code=201,
            data={
                "id": resource.id,
                "title": resource.title,
                "category_id": resource.category_id,
                "created_at": resource.created_at
            }
        )
    except HTTPException as e:
        logger.error(f"HTTP error creating resource {e.status_code}: {str(e)}", exc_info=True)
        return fail_response(message="Invalid Request", status_code=e.status_code)
    except Exception as e:
        logger.error(f"Error creating resource: {str(e)}", exc_info=True)
        return fail_response(message="Failed to create resource", status_code=500)