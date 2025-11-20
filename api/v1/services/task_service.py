from sqlalchemy.orm import Session
from api.v1.models.task import Task
from api.v1.models.user.user import User
from api.utils.logger import logger


def create_task(request, db: Session, current_user: User):
    """Create a new task for the current user"""

    try:
        logger.info(f"Creating task for user {current_user.id}")

        task = Task(
            user_id=current_user.id,
            name=request.name,
            description=request.description,
            due_date=request.due_date,
            status="pending",
            completed_at=None
        )

        task.insert(db)  # Using BaseModel CRUD

        logger.info(f"Task created successfully for user {current_user.id}")

        return task

    except Exception as e:
        logger.error(f"Error creating task for user {current_user.id}: {e}")
        raise