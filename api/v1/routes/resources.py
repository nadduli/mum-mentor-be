from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session
import math
from uuid import UUID
from api.db.database import get_db
from api.v1.services.resource import ResourceService
from api.v1.schemas.resource import PaginatedResourceResponse, ResourceCreate, CategoryCreate, ResourceUpdate
from api.utils.deps import get_current_user
from api.utils.logger import logger
from api.v1.models.user.user import User
from api.utils.responses import success_response, fail_response
from typing import Optional

router = APIRouter(prefix="/resources", tags=["Resources"])

@router.get("/", status_code=status.HTTP_200_OK, response_model=PaginatedResourceResponse)
async def get_all_resources(
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

@router.get("/search", status_code=status.HTTP_200_OK, response_model=PaginatedResourceResponse)
async def search_resources(
    q: str = Query(..., min_length=1, description="Search term"),
    category_id: Optional[UUID] = Query(None, description="Filter by category ID"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    session: Session = Depends(get_db)
):
    """
    Search resources by title, content, or category name.
    """
    try:
        resources, total = ResourceService.search_resources(
            session=session, 
            query_str=q, 
            page=page, 
            limit=limit,
            category_id=category_id
        )
        
        total_pages = math.ceil(total / limit) if limit > 0 else 0

        return {
            "status": "success",
            "message": "Search results retrieved successfully",
            "data": resources,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages
        }
    except Exception as e:
        logger.error(f"Search failed: {str(e)}", exc_info=True)
        return fail_response(message="Search failed", status_code=500)

@router.post("/categories", status_code=status.HTTP_201_CREATED)
async def create_category(
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
        return fail_response(message=e.detail, status_code=e.status_code)
    except Exception as e:
        logger.error(f"Error creating category: {str(e)}", exc_info=True)
        return fail_response(message="Failed to create category", status_code=500)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_resource(
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
        return fail_response(message=e.detail, status_code=e.status_code)
    except Exception as e:
        logger.error(f"Error creating resource: {str(e)}", exc_info=True)
        return fail_response(message="Failed to create resource", status_code=500)
    
@router.delete("/{resource_id}", status_code=status.HTTP_200_OK)
async def delete_resource(
    resource_id: UUID,
    session: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a resource by ID."""
    try:
        ResourceService.delete_resource(session, resource_id)
        return success_response(
            message="Resource deleted successfully",
            status_code=200,
            data=None
        )
    except HTTPException as e:
        logger.error(f"HTTP error deleting resource {e.status_code}: {str(e)}", exc_info=True)
        return fail_response(message=e.detail, status_code=e.status_code)
    except Exception as e:
        logger.error(f"Error deleting resource: {str(e)}", exc_info=True)
        return fail_response(message="Failed to delete resource", status_code=500)
    
@router.patch("/{resource_id}", status_code=status.HTTP_200_OK)
async def update_resource(
    resource_id: UUID,
    schema: ResourceUpdate,
    session: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update a resource by ID."""
    try:
        resource = ResourceService.update_resource(session, resource_id, schema)
        return success_response(
            message="Resource updated successfully",
            status_code=200,
            data={
                "id": resource.id,
                "title": resource.title,
                "category_id": resource.category_id,
                "created_at": resource.created_at,
                "updated_at": resource.updated_at
            }
        )
    except HTTPException as e:
        logger.error(f"HTTP error updating resource {e.status_code}: {str(e)}", exc_info=True)
        return fail_response(message=e.detail, status_code=e.status_code)
    except Exception as e:
        logger.error(f"Error updating resource: {str(e)}", exc_info=True)
        return fail_response(message="Failed to update resource", status_code=500)
@router.get("/categories", status_code=status.HTTP_200_OK)
async def get_all_categories(
    session: Session = Depends(get_db)
):
    """Get all resource categories."""
    try:
        categories = ResourceService.get_all_categories(session)
        data = [{"id": cat.id, "name": cat.name} for cat in categories]

        return success_response(
            message="Categories retrieved successfully",
            status_code=200,
            data={"categories":data}
        )
    except Exception as e:
        logger.error(f"Error retrieving categories: {str(e)}", exc_info=True)
        return fail_response(message="Failed to retrieve categories", status_code=500)
    
@router.get("/{resource_id}", status_code=status.HTTP_200_OK)
async def get_resource_by_id(
    resource_id: UUID,
    session: Session = Depends(get_db)
):
    """Get a resource by ID."""
    try:
        resource = ResourceService.get_resource_by_id(session, resource_id)
        return success_response(
            message="Resource retrieved successfully",
            status_code=200,
            data={
                "id": resource.id,
                "title": resource.title,
                "content": resource.content,
                "category_id": resource.category_id,
                "created_at": resource.created_at,
                "updated_at": resource.updated_at
            }
        )
    except HTTPException as e:
        logger.error(f"HTTP error retrieving resource {e.status_code}: {str(e)}", exc_info=True)
        return fail_response(message=e.detail, status_code=e.status_code)
    except Exception as e:
        logger.error(f"Error retrieving resource: {str(e)}", exc_info=True)
        return fail_response(message="Failed to retrieve resource", status_code=500)
    
    
@router.delete("/categories/{category_id}", status_code=status.HTTP_200_OK)
async def delete_category(
    category_id: UUID,
    session: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a resource category by ID."""
    try:
        ResourceService.delete_category(session, category_id)
        return success_response(
            message="Category deleted successfully",
            status_code=200,
            data=None
        )
    except HTTPException as e:
        logger.error(f"HTTP error deleting category {e.status_code}: {str(e)}", exc_info=True)
        return fail_response(message=e.detail, status_code=e.status_code)
    except Exception as e:
        logger.error(f"Error deleting category: {str(e)}", exc_info=True)
        return fail_response(message="Failed to delete category", status_code=500)
    

@router.patch("/categories/{category_id}", status_code=status.HTTP_200_OK)
async def update_category(
    category_id: UUID,
    schema: CategoryCreate,
    session: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update a resource category by ID."""
    try:
        category = ResourceService.update_category(session, category_id, schema)
        return success_response(
            message="Category updated successfully",
            status_code=200,
            data={
                "id": category.id,
                "name": category.name
            }
        )
    except HTTPException as e:
        logger.error(f"HTTP error updating category {e.status_code}: {str(e)}", exc_info=True)
        return fail_response(message=e.detail, status_code=e.status_code)
    except Exception as e:
        logger.error(f"Error updating category: {str(e)}", exc_info=True)
        return fail_response(message="Failed to update category", status_code=500)
    
@router.get("/categories/{category_id}", status_code=status.HTTP_200_OK)
async def get_category_by_id(
    category_id: UUID,
    session: Session = Depends(get_db)
):
    """Get a resource category by ID."""
    try:
        category = ResourceService.get_category_by_id(session, category_id)
        return success_response(
            message="Category retrieved successfully",
            status_code=200,
            data={
                "id": category.id,
                "name": category.name
            }
        )
    except HTTPException as e:
        logger.error(f"HTTP error retrieving category {e.status_code}: {str(e)}", exc_info=True)
        return fail_response(message=e.detail, status_code=e.status_code)
    except Exception as e:
        logger.error(f"Error retrieving category: {str(e)}", exc_info=True)
        return fail_response(message="Failed to retrieve category", status_code=500)
    
@router.get("/categories/{category_id}/resources", status_code=status.HTTP_200_OK, response_model=PaginatedResourceResponse)
async def get_resources_by_category(
    category_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    session: Session = Depends(get_db)
):
    """
    Get resources by category with pagination.
    Includes media and category details.
    """
    try:
        resources, total = ResourceService.get_resources_by_category(session, category_id, page, limit)
        
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
    except HTTPException as e:
        logger.error(f"HTTP error retrieving resources by category {e.status_code}: {str(e)}", exc_info=True)
        return fail_response(message=e.detail, status_code=e.status_code)
    except Exception as e:
        logger.error(f"Error retrieving resources by category: {str(e)}", exc_info=True)
        return fail_response(message="Failed to retrieve resources by category", status_code=500)
    