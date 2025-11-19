import logging
from typing import Optional, Tuple, List

from sqlalchemy import select, or_, func, String
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.v1.models.user.user import FAQ
from api.utils.logger import logger



class FAQService:
    """Service class for FAQ-related operations"""

    @staticmethod
    def fetch_faqs(
            session: Session,
            category: Optional[str],
            search: Optional[str],
            limit: int,
            offset: int,
    ):
        """
        Fetch FAQs with optional category and search filters.

        Returns:
            (faqs, None, total_count) on success
            (None, error_message, None) on failure
        """
        try:
            logger.info(
                "Fetching FAQs | category=%s | search=%s | limit=%s | offset=%s",
                category,
                search,
                limit,
                offset,
            )

            # Base query
            query = select(FAQ).where(FAQ.is_published.is_(True))
            count_query = select(func.count(FAQ.id)).where(FAQ.is_published.is_(True))

            # Category filter
            if category:
                query = query.where(FAQ.category.ilike(category))
                count_query = count_query.where(FAQ.category.ilike(category))
                logger.debug("Applied category filter: %s", category)

            # Search filter
            if search:
                pattern = f"%{search}%"
                search_filter = or_(
                    FAQ.question.ilike(pattern),
                    FAQ.answer.ilike(pattern),
                    FAQ.keywords.cast(String).ilike(pattern),
                )
                query = query.where(search_filter)
                count_query = count_query.where(search_filter)
                logger.debug("Applied search filter: %s", pattern)

            # Pagination + ordering
            query = query.order_by(FAQ.order_index.asc()).limit(limit).offset(offset)

            # Run queries
            result = session.execute(query)
            faqs = result.scalars().all()

            total = session.scalar(count_query)

            logger.info("Fetched %s FAQs (total=%s)", len(faqs), total)

            return faqs, None, total

        except SQLAlchemyError as db_err:
            session.rollback()
            logger.error("Database error while fetching FAQs: %s", str(db_err), exc_info=True)
            return None, "A database error occurred while fetching FAQs", None

        except Exception as e:
            session.rollback()
            logger.error("Unexpected error fetching FAQs: %s", str(e), exc_info=True)
            return None, "An unexpected error occurred while fetching FAQs", None