from sqlalchemy.orm import Session
from api.v1.models.task import Task
from api.v1.models.user.user import User
from api.utils.logger import logger
from uuid import UUID
from api.v1.schemas.task import EditTaskRequest
from typing import Optional, Tuple


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


class TaskService:
    """Service for task operations"""

    @staticmethod
    def get_task_by_id(db: Session, task_id: UUID, user_id: UUID) -> Optional[Task]:
        """
        Retrieve a task by ID for a specific user.
        
        Args:
            db: Database session
            task_id: UUID of the task
            user_id: UUID of the user who owns the task
            
        Returns:
            Task object if found, None otherwise
        """
        try:
            task = db.query(Task).filter(
                Task.id == task_id,
                Task.user_id == user_id
            ).first()
            return task
        except Exception as e:
            logger.error(f"Error retrieving task: {str(e)}")
            return None

    @staticmethod
    def update_task(
        db: Session, 
        task: Task, 
        update_data: EditTaskRequest
    ) -> Tuple[Optional[Task], Optional[str]]:
        """
        Update a task with the provided data.
        
        Args:
            db: Database session
            task: Task object to update
            update_data: EditTaskRequest with fields to update
            
        Returns:
            Tuple of (updated_task, error_message)
        """
        try:
            # Update only the fields that are provided
            update_dict = update_data.model_dump(exclude_unset=True)
            
            for field, value in update_dict.items():
                setattr(task, field, value)
            
            db.commit()
            db.refresh(task)
            
            logger.info(f"Task {task.id} updated successfully")
            return task, None
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating task: {str(e)}")
            return None, str(e)
