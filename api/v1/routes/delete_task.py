from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID

from api.db.database import get_db
from api.utils.deps import get_current_user
from api.v1.models.user.user import User
from api.v1.services.task_service import TaskService
from api.utils.responses import success_response, fail_response
from api.utils.logger import logger

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"]
)

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Hard delete a task.

    This endpoint allows authenticated users to permanently delete their tasks.
    Users can only delete tasks that belong to them.

    Args:
        task_id: UUID of the task to delete
        db: Database session
        current_user: Authenticated user from JWT token

    Returns:
        204 No Content on successful deletion

    Raises:
        404: Task not found or doesn't belong to user
        500: Internal server error
    """
    try:
        # Retrieve the task
        task = TaskService.get_task_by_id(db, task_id, current_user.id)
        
        if not task:
            logger.warning(f"Task {task_id} not found for user {current_user.id}")
            return fail_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Task not found"
            )
        
        # Hard delete the task
        success = TaskService.delete_task(db, task)
        
        if not success:
            logger.error(f"Failed to delete task {task_id} for user {current_user.id}")
            return fail_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Failed to delete task"
            )
        
        logger.info(f"Task {task_id} deleted successfully by user {current_user.id}")
        # Return 204 No Content as requested
        return None
        
    except Exception as e:
        logger.error(f"Unexpected error deleting task: {str(e)}")
        return fail_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="An unexpected error occurred"
        )