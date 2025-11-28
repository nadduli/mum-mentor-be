from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_
from typing import Tuple, List, Optional
from api.utils.logger import logger
from fastapi import HTTPException, status
from api.v1.models.resource.resource import Resource
from api.v1.models.resource.resource_category import ResourceCategory
from api.v1.schemas.resource import ResourceCreate, CategoryCreate, ResourceUpdate
from uuid import UUID

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
    
    @staticmethod
    def delete_resource(session: Session, resource_id) -> None:
        """Delete a resource by ID"""
        resource = Resource.fetch_one(session, id=resource_id)
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )
        resource.delete(session)

    @staticmethod
    def update_resource(session: Session, resource_id, schema: ResourceUpdate) -> Resource:
        """Update an existing resource"""
        resource = Resource.fetch_one(session, id=resource_id)
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )
        

        resource.title = schema.title
        resource.content = schema.content

        session.commit()
        session.refresh(resource)
        return resource
    
    @staticmethod
    def get_resource_by_id(session: Session, resource_id) -> Resource:
        """Fetch a resource by ID"""
        resource = Resource.fetch_one(session, id=resource_id)
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )
        return resource
    
    @staticmethod
    def get_all_categories(session: Session) -> List[ResourceCategory]:
        """Fetch all resource categories"""
        categories = session.query(ResourceCategory).all()
        return categories
    
    @staticmethod
    def get_category_by_id(session: Session, category_id) -> ResourceCategory:
        """Fetch a resource category by ID"""
        category = ResourceCategory.fetch_one(session, id=category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource Category not found"
            )
        return category
    
    @staticmethod
    def delete_category(session: Session, category_id) -> None:
        """Delete a resource category by ID"""
        category = ResourceCategory.fetch_one(session, id=category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource Category not found"
            )
        category.delete(session)


    @staticmethod
    def update_category(session: Session, category_id, schema: CategoryCreate) -> ResourceCategory:
        """Update an existing resource category"""
        category = ResourceCategory.fetch_one(session, id=category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource Category not found"
            )

        existing_cat = ResourceCategory.fetch_one(session, name=schema.name)
        if existing_cat and existing_cat.id != category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category '{schema.name}' already exists"
            )

        category.name = schema.name

        session.commit()
        session.refresh(category)
        return category
    
    @staticmethod
    def get_resources_by_category(session: Session, category_id: UUID, page: int, limit: int) -> Tuple[List[Resource], int]:
        """
        Fetches resources by category with their related media and category data efficiently.
        """
        skip = (page - 1) * limit
        logger.info(f"Fetching resources for category_id={category_id} page={page} limit={limit}")

        query = session.query(Resource).options(
            joinedload(Resource.category),
            joinedload(Resource.media)
        ).filter(Resource.category_id == category_id)

        total = query.count()

        resources = query.order_by(desc(Resource.created_at)).offset(skip).limit(limit).all()
        
        return resources, total
    
    @staticmethod
    def get_resources_by_title(session: Session, title_substr: str, page: int, limit: int) -> Tuple[List[Resource], int]:
        """
        Fetches resources by title substring with their related media and category data efficiently.
        """
        skip = (page - 1) * limit
        logger.info(f"Fetching resources with title containing '{title_substr}' page={page} limit={limit}")

        query = session.query(Resource).options(
            joinedload(Resource.category),
            joinedload(Resource.media)
        ).filter(Resource.title.ilike(f"%{title_substr}%"))

        total = query.count()

        resources = query.order_by(desc(Resource.created_at)).offset(skip).limit(limit).all()
        
        return resources, total
    
    @staticmethod
    def search_resources(
        session: Session, 
        query_str: str, 
        page: int, 
        limit: int,
        category_id: Optional[UUID] = None
    ) -> Tuple[List[Resource], int]:
        """
        Search resources by title, content, or category name.
        Optional: Filter by specific category_id.
        """
        skip = (page - 1) * limit
        logger.info(f"Search query='{query_str}' cat={category_id} page={page}")

        query = session.query(Resource).options(
            joinedload(Resource.category),
            joinedload(Resource.media)
        )

        query = query.join(Resource.category)

        if query_str:
            search_filter = or_(
                Resource.title.ilike(f"%{query_str}%"),
                Resource.content.ilike(f"%{query_str}%"),
                ResourceCategory.name.ilike(f"%{query_str}%")
            )
            query = query.filter(search_filter)

        if category_id:
            query = query.filter(Resource.category_id == category_id)

        total = query.count()
        resources = query.order_by(desc(Resource.created_at)).offset(skip).limit(limit).all()
        
        return resources, total
