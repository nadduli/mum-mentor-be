from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.deps import get_current_user
from api.v1.models.user.user import User
from api.v1.schemas.task import CreateTaskRequest
from api.v1.services.task_service import create_task
from api.utils.responses import success_response
from api.utils.logger import logger

router = APIRouter(tags=["Tasks"])

@router.post("/create_task", status_code=status.HTTP_201_CREATED)
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