
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.deps import get_current_user
from api.v1.schemas.task_list import TaskListResponse, TaskItem, Pagination
from api.v1.services.task_list import TaskService
from api.utils.responses import success_response, fail_response


router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/", response_model=TaskListResponse)
def list_tasks(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1),
    task_status: str | None = "pending",
    session: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    tasks, total, error = TaskService.list_tasks(
        session=session,
        user_id=user.id,
        page=page,
        per_page=per_page,
        status=task_status
    )

    if error:
        return fail_response(
            status_code=500,
            message="Failed to fetch tasks"
        )

    details = [
        TaskItem(
            name=t.name,
            description=t.description,
            due_date=t.due_date,
            status=t.status,
            completed_at=t.completed_at,
            created_at=t.created_at,
            updated_at=t.updated_at
        )
        for t in tasks
    ]

    pagination = Pagination(
        page=page,
        per_page=per_page,
        total_count=total,
        next=page + 1 if (page * per_page) < total else None,
        prev=page - 1 if page > 1 else None,
    )

    return success_response(
        status_code=200,
        message="Tasks retrieved successfully",
        data={
            "details": [task.model_dump() for task in details],
            "pagination": pagination.model_dump(),
        }
    )
