from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, select
from typing import Tuple, List

from api.v1.models.resource.resource import Resource
from api.utils.logger import logger

class ResourceService:
    
    @staticmethod
    def get_all_resources(session: Session, page: int, limit: int) -> Tuple[List[Resource], int]:
        """
        Fetches resources with their related media and category data efficiently.
        """
        skip = (page - 1) * limit
        logger.info(f"Fetching resources page={page} limit={limit}")

        query = session.query(Resource).options(
            joinedload(Resource.category),
            joinedload(Resource.media)
        )

        total = query.count()

        resources = query.order_by(desc(Resource.created_at)).offset(skip).limit(limit).all()
        
        return resources, total

    @staticmethod
    def search_by_title(
            session: Session,
            title: str,
            page: int,
            limit: int
    ):
        """
        Search resources by partial + case-insensitive title match.
        """

        # Paginated query
        stmt = (
            select(Resource)
            .where(Resource.title.ilike(f"%{title}%"))
            .offset((page - 1) * limit)
            .limit(limit)
        )
        resources = session.scalars(stmt).all()

        # Total count
        count_stmt = select(Resource).where(Resource.title.ilike(f"%{title}%"))
        total = len(session.scalars(count_stmt).all())

        return resources, total