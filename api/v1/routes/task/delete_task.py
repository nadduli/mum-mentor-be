from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID

from api.db.database import get_db
from api.utils.deps import get_current_user
from api.v1.models.user.user import User
from api.v1.services.task_service import TaskService
from api.utils.responses import success_response, fail_response
from api.utils.logger import logger

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.delete("/{task_id}")
def delete_task_endpoint(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a task"""
    try:
        task_service = TaskService(db)
        task = task_service.get_task_by_id(task_id, current_user.id)
        
        if not task:
            return fail_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Task not found"
            )
        
        success = TaskService.delete_task(db, task)
        
        if success:
            return success_response(
                status_code=status.HTTP_200_OK,
                message="Task deleted successfully"
            )
        else:
            return fail_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Failed to delete task"
            )
            
    except Exception as e:
        logger.error(f"Error deleting task: {str(e)}")
        return fail_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="An error occurred while deleting the task"
        )