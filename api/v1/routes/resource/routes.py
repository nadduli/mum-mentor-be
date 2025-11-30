"""
This module contains the API endpoints for managing resources.
"""

import math
import uuid

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.deps import get_current_user
from api.utils.responses import fail_response, success_response
from api.v1.models.user.user import User
from api.v1.schemas.resource import (
    CreateResourceBookmark,
    PaginatedResourceResponse,
    ResourceResponse,
)
from api.v1.services.resource import ResourceService
from api.v1.services.resource_media import ResourceMediaService
from api.v1.services.create_resource_bookmark import create_resource_bookmark

resource_router = APIRouter(prefix="/resources", tags=["Resources"])


@resource_router.get("/media/{media_id}", status_code=status.HTTP_200_OK)
def view_resource_media(
    media_id: uuid.UUID,
    session: Session = Depends(get_db),
):
    """
    View a single media file (photo or video) from a community post.

    This endpoint retrieves details of a specific media file associated with
    a community resource post.

    **Path Parameters:**
    - media_id (required): UUID of the media file to view

    **Authentication:**
    - Requires valid access token

    **Returns:**
    - Media details including:
      - id: Media UUID
      - resource_id: UUID of the post this media belongs to
      - url: Direct URL to the media file
      - media_type: Either "photo" or "video"

    **Example Response:**
    ```json
    {
      "status": "success",
      "status_code": 200,
      "message": "Media retrieved successfully",
      "data": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "resource_id": "987fcdeb-51a2-43f7-b123-456789abcdef",
        "url": "https://example.com/media/video.mp4",
        "media_type": "video"
      }
    }
    ```

    **Error Responses:**
    - 404: Media not found
    - 401: Unauthorized (invalid or missing token)
    """
    media_data = ResourceMediaService.get_media_by_id(session, media_id)

    return success_response(
        status_code=status.HTTP_200_OK,
        message="Media retrieved successfully",
        data=media_data,
    )


@resource_router.get(
    "/", status_code=status.HTTP_200_OK, response_model=PaginatedResourceResponse
)
def get_all_resources(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    session: Session = Depends(get_db),
):
    """
    Get all resources (videos, articles) with pagination.
    Includes media and category details.
    """
    resources, total = ResourceService.get_resources(session, page, limit)

    total_pages = math.ceil(total / limit) if limit > 0 else 0

    return {
        "status": "success",
        "message": "Resources retrieved successfully",
        "data": resources,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
    }


@resource_router.get("/search", status_code=status.HTTP_200_OK)
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
            session=session, title=title, page=page, limit=limit
        )

        if not resources:
            return fail_response(
                status_code=404, message="No resources found", context={"title": title}
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
            "total_pages": total_pages,
        }

        return success_response(
            status_code=200, message="Resources retrieved successfully", data=payload
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search resources",
        ) from e


@resource_router.post("/bookmarks/")
async def save_resource_for_later(
    payload: CreateResourceBookmark,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a bookmark for a resource for the current user.

    This endpoint allows an authenticated user to save a resource for later access (bookmark).
    It expects a payload with the resource ID, and will associate the resource with the user.
    Returns a success response with the bookmark details, or an error if the operation fails.
    """
    try:
        new_bookmark = create_resource_bookmark(
            db, current_user.id, payload.resource_id
        )
        return success_response(
            status_code=status.HTTP_201_CREATED,
            message="Successfully created resource for later",
            data=new_bookmark,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong while trying to save your resource bookmark",
        ) from e
