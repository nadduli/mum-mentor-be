from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.v1.schemas.task import TaskResponse, TaskStatusUpdate
from api.v1.services.task_service import TaskService
from api.utils.deps import get_current_user, get_db
from uuid import UUID

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.patch("/{task_id}/status", response_model=TaskResponse)
def toggle_task_completion(
    task_id: str,
    status_update: TaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Toggles the completion status of a task.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        task_uuid = UUID(task_id)
        user_uuid = UUID(current_user["id"])
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid UUID format",
        )

    task_service = TaskService(db)
    task = task_service.toggle_completion(
        task_id=task_uuid, completed=status_update.completed, user_id=user_uuid
    )
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return task
