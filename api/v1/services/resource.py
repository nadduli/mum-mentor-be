from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import Tuple, List
from api.utils.logger import logger
from fastapi import HTTPException, status
from api.v1.models.resource.resource import Resource
from api.v1.models.resource.resource_category import ResourceCategory
from api.v1.schemas.resource import ResourceCreate, CategoryCreate

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
    def create_category(session: Session, schema: CategoryCreate) -> ResourceCategory:
        """Create a new resource category"""
        existing_cat = ResourceCategory.fetch_one(session, name=schema.name)
        if existing_cat:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category '{schema.name}' already exists"
            )

        new_category = ResourceCategory(name=schema.name)
        return new_category.insert(session)

    @staticmethod
    def create_resource(session: Session, schema: ResourceCreate) -> Resource:
        """Create a new resource"""
        category = ResourceCategory.fetch_one(session, id=schema.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource Category not found"
            )

        new_resource = Resource(
            title=schema.title,
            content=schema.content,
            category_id=schema.category_id
        )
        return new_resource.insert(session)