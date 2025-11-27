from fastapi import APIRouter, status

journal_entry_router = APIRouter()

@journal_entry_router.get("/")
async def get_entry_by_category(category: str):
    if category is None:
       return status.HTTP_400_BAD_REQUEST # with response body, category is absent
    
    
    pass
