import logging

from sqlalchemy import select, or_, func, String
from sqlalchemy.orm import Session
from api.v1.models.faq.faq import FAQ
from api.utils.logger import logger



class FAQService:

    @staticmethod
    def fetch_faqs(
        session: Session,
        category: str | None,
        search: str | None,
        limit: int,
        offset: int,
    ):
        logger.info(
            f"Fetching FAQs | category={category} | search={search} | "
            f"limit={limit} | offset={offset}"
        )

        # Base queries
        query = select(FAQ).where(FAQ.is_published.is_(True))
        count_query = select(func.count(FAQ.id)).where(FAQ.is_published.is_(True))

        # Category filter
        if category:
            query = query.where(FAQ.category.ilike(category))
            count_query = count_query.where(FAQ.category.ilike(category))

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

        query = query.order_by(FAQ.order_index.asc()).limit(limit).offset(offset)

        result = session.execute(query)
        faqs = result.scalars().all()

        total = session.scalar(count_query)

        logger.info(f"Fetched {len(faqs)} FAQs (total: {total})")

        return faqs, total