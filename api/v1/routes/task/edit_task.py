from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID

from api.db.database import get_db
from api.utils.deps import get_current_user
from api.v1.models.user.user import User
from api.v1.schemas.task import EditTaskRequest
from api.v1.services.task_service import TaskService
from api.utils.responses import success_response, fail_response
from api.utils.logger import logger

router = APIRouter(tags=["Tasks"])

@router.patch("/{task_id}")
def edit_task(
    task_id: UUID,
    request_data: EditTaskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Edit an existing task.
    """
    try:

        task_service = TaskService(db)
        task = task_service.get_task_by_id(task_id, current_user.id)
        
        if not task:
            logger.warning(f"Task {task_id} not found for user {current_user.id}")
            return fail_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Task not found"
            )
    
        
        updated_task, error = task_service.update_task(task, request_data)
        
        if error:
            logger.error(f"Error updating task {task_id}: {error}")
            return fail_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Failed to update task",
                data={"error": error}
            )
        
        response_data = {
            "id": str(updated_task.id),
            "name": updated_task.name,
            "description": updated_task.description,
            "due_date": updated_task.due_date.isoformat() if updated_task.due_date else None,
            "status": updated_task.status,
            "completed_at": updated_task.completed_at.isoformat() if updated_task.completed_at else None,
            "created_at": updated_task.created_at.isoformat(),
            "updated_at": updated_task.updated_at.isoformat()
        }
        
        logger.info(f"Task {task_id} updated successfully by user {current_user.id}")
        return success_response(
            status_code=status.HTTP_200_OK,
            message="Task updated successfully",
            data=response_data
        )
        
    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}")
        return fail_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=str(ve)
        )
    except Exception as e:
        logger.error(f"Unexpected error editing task: {str(e)}")
        return fail_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="An unexpected error occurred"
        )