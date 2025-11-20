from uuid import UUID
from typing import Optional, Tuple
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from api.v1.models.task.task import Task
from api.v1.schemas.task import EditTaskRequest
from api.utils.logger import logger


class TaskService:
    """Service for task operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_task_by_id(self, task_id: UUID, user_id: UUID) -> Optional[Task]:
        """
        Retrieve a task by ID for a specific user.

        Args:
            task_id: UUID of the task
            user_id: UUID of the user who owns the task

        Returns:
            Task object if found, None otherwise
        """
        try:
            task = (
                self.db.query(Task)
                .filter(Task.id == task_id, Task.user_id == user_id)
                .first()
            )
            return task
        except Exception as e:
            logger.error(f"Error retrieving task: {str(e)}")
            return None

    def toggle_completion(
        self, task_id: UUID, completed: bool, user_id: UUID
    ) -> Optional[Task]:
        """
        Toggles the completion status of a task.

        Args:
            task_id: UUID of the task
            completed: Boolean indicating the completion status
            user_id: UUID of the user who owns the task

        Returns:
            Updated task object if found, None otherwise
        """
        task = self.get_task_by_id(task_id, user_id)
        if not task:
            return None

        if completed:
            task.status = "completed"
            task.completed_at = datetime.now(timezone.utc)
        else:
            task.status = "pending"
            task.completed_at = None

        try:
            self.db.commit()
            self.db.refresh(task)
            return task
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error toggling task completion: {str(e)}")
            return None

    def update_task(
        self, task: Task, update_data: EditTaskRequest
    ) -> Tuple[Optional[Task], Optional[str]]:
        """
        Update a task with the provided data.

        Args:
            task: Task object to update
            update_data: EditTaskRequest with fields to update

        Returns:
            Tuple of (updated_task, error_message)
        """
        try:
            update_dict = update_data.model_dump(exclude_unset=True)

            if "status" in update_dict:
                task.status = update_dict["status"]
                if task.status == "completed":
                    task.completed_at = datetime.now(timezone.utc)
                else:
                    task.completed_at = None
                del update_dict["status"]

            if "due_date" in update_dict and update_dict["due_date"] is not None:
                task.due_date = datetime.fromisoformat(update_dict["due_date"].replace('Z', '+00:00'))
                del update_dict["due_date"]

            for field, value in update_dict.items():
                setattr(task, field, value)

            self.db.commit()
            self.db.refresh(task)

            logger.info(f"Task {task.id} updated successfully")
            return task, None

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating task: {str(e)}")
            return None, str(e)
