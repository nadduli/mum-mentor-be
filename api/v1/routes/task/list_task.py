from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from api.db.database import get_db
from api.utils.deps import get_current_user
from api.v1.models.user.user import User
from api.v1.services.task_service import TaskService
from api.utils.responses import success_response
from api.utils.logger import logger

router = APIRouter(tags=["Tasks"])

@router.get("/tasks/")
def list_tasks(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    task_status: Optional[str] = Query(None, description="Filter by status: 'pending' or 'completed'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get paginated list of tasks for the current user with optional status filter.
    """
    try:
        logger.info(f"Fetching tasks | user_id={current_user.id} | page={page} | per_page={per_page} | status={task_status}")
        
        # Validate status filter
        if task_status and task_status not in ['pending', 'completed']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status must be either 'pending' or 'completed'"
            )
        
        task_service = TaskService(db)
        tasks, total_count = task_service.get_user_tasks(
            user_id=current_user.id,
            page=page,
            per_page=per_page,
            status=task_status
        )
        
        # Prepare response data
        tasks_data = []
        for task in tasks:
            tasks_data.append({
                "id": str(task.id),
                "name": task.name,
                "description": task.description,
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "status": task.status,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat()
            })
        
        # Calculate pagination info
        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
        
        response_data = {
            "tasks": tasks_data,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_items": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
        
        return success_response(
            status_code=status.HTTP_200_OK,
            message="Tasks retrieved successfully",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing tasks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving tasks"
        )