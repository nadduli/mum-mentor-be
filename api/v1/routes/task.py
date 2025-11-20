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
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.utils.deps import get_current_user
from api.v1.schemas.task import CreateTaskRequest
from api.v1.services.task_service import create_task
from api.utils.responses import success_response
from api.utils.logger import logger
from api.v1.models.user.user import User

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.post("/")
def create_task_endpoint(
    request: CreateTaskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logger.info("Entered create_task endpoint")
    task = create_task(request, db, current_user)

    return success_response(
        201,
        "Task created successfully",
        {
            "id": str(task.id),
            "name": task.name,
            "description": task.description,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "status": task.status,
            "completed_at": None,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
        }
    )
