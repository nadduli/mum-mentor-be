from fastapi import APIRouter
from .get_entry_by_category import journal_entry_router as get_by_category_router
from .create_journal_entry import router as create_journal_router
from .edit_journal_entry import router as edit_journal_router

journal_entry_router = APIRouter()
journal_entry_router.include_router(create_journal_router)
journal_entry_router.include_router(get_by_category_router)

router = APIRouter()
router.include_router(create_journal_router)
router.include_router(get_by_category_router)
router.include_router(edit_journal_router)

__all__ = ["journal_entry_router", "router"]