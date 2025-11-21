from sqlalchemy import select, func
from sqlalchemy.orm import Session
from api.v1.models.task import Task
from api.utils.logger import logger


class TaskService:

    @staticmethod
    def list_tasks(
        session: Session,
        user_id: int,
        page: int,
        per_page: int,
        status: str | None
    ):
        try:
            logger.info(
                "Fetching tasks | user_id=%s | page=%s | per_page=%s | status=%s",
                user_id, page, per_page, status
            )

            # Build filter for fetch_all
            filters = {"user_id": user_id}
            if status:
                filters["status"] = status

            # First: get total count
            total_query = select(func.count(Task.id)).filter_by(**filters)
            total = session.execute(total_query).scalar() or 0

            # Second: fetch paginated tasks
            query = (
                select(Task)
                .filter_by(**filters)
                .order_by(Task.due_date.asc().nulls_last())
                .limit(per_page)
                .offset((page - 1) * per_page)
            )

            tasks = session.execute(query).scalars().all()

            return tasks, total, None

        except Exception as e:
            logger.error("Task fetch failed: %s", str(e))
            return None, None, str(e)