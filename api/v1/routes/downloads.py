from fastapi import APIRouter, Depends, Request, Query, status
from sqlalchemy.orm import Session
from datetime import datetime
from api.db.database import get_db
from api.v1.schemas.downloads import DownloadTrackRequest, DownloadTrackResponse
from api.v1.services.download_tracking import log_download_event, get_download_stats
from api.utils.responses import success_response, fail_response

router = APIRouter(prefix="/downloads", tags=["downloads"])

@router.post("/track", response_model=DownloadTrackResponse, status_code=status.HTTP_201_CREATED)
async def track_download(payload: DownloadTrackRequest, request: Request, db: Session = Depends(get_db)):
    try:
        # Placeholder: integrate auth later; user_id None for anonymous
        event = log_download_event(db, request, payload, user_id=None, session_id=None)
        return event
    except Exception as e:
        return fail_response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, message="Failed to track download")

@router.get("/stats")
async def download_stats(
    db: Session = Depends(get_db),
    from_dt: datetime | None = Query(None),
    to_dt: datetime | None = Query(None),
    group_by: str = Query("download_type"),
):
    try:
        data = get_download_stats(db, from_dt=from_dt, to_dt=to_dt, group_by=group_by)
        return success_response(status_code=200, message="Download stats", data=data)
    except AttributeError:
        return fail_response(status_code=400, message="Invalid group_by field")
    except Exception:
        return fail_response(status_code=500, message="Failed to fetch stats")
