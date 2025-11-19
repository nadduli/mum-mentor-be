from sqlalchemy.orm import Session
from fastapi import Request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from api.v1.models.downloads import DownloadEvent
from api.v1.schemas.downloads import DownloadTrackRequest
from api.utils.logger import logger

MOBILE_KEYWORDS = ["mobile", "android", "iphone"]
TABLET_KEYWORDS = ["ipad", "tablet"]


def _infer_device_type(user_agent: str | None) -> str | None:
    if not user_agent:
        return None
    ua = user_agent.lower()
    if any(k in ua for k in MOBILE_KEYWORDS):
        return "mobile"
    if any(k in ua for k in TABLET_KEYWORDS):
        return "tablet"
    return "desktop"


def log_download_event(
    db: Session,
    request: Request,
    payload: DownloadTrackRequest,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Tuple[Optional[DownloadEvent], Optional[str]]:
    referrer = request.headers.get("referer") or request.headers.get("referrer")
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    device_type = _infer_device_type(user_agent)

    try:
        event = DownloadEvent(
            user_id=user_id,
            session_id=session_id,
            download_type=payload.download_type,
            resource_id=payload.resource_id,
            file_name=payload.file_name,
            file_url=payload.file_url,
            source=payload.source,
            referrer=referrer,
            ip_address=ip_address,
            user_agent=user_agent,
            device_type=device_type,
            extra_metadata=payload.extra_metadata,
            occurred_at=datetime.now(timezone.utc),
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        logger.info("download_event_logged",
                    extra={
                        "download_type": event.download_type,
                        "resource_id": event.resource_id,
                        "user_id": str(event.user_id) if event.user_id else None,
                    })
        return event, None
    except Exception as e:
        db.rollback()
        logger.error(f"download_event_failed: {e}")
        return None, "Failed to track download"


def get_download_stats(
    db: Session,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
    group_by: str = "download_type",
) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    from sqlalchemy import func
    try:
        # Validate group_by
        group_col = getattr(DownloadEvent, group_by)
    except AttributeError:
        return None, "Invalid group_by field"

    from sqlalchemy import func
    try:
        query = db.query(group_col, func.count(DownloadEvent.id))
        if from_dt:
            query = query.filter(DownloadEvent.occurred_at >= from_dt)
        if to_dt:
            query = query.filter(DownloadEvent.occurred_at <= to_dt)
        query = query.group_by(group_col)
        rows = query.all()
        data = [{group_by: r[0], "count": r[1]} for r in rows]
        return data, None
    except Exception as e:
        logger.error(f"download_stats_failed: {e}")
        return None, "Failed to fetch stats"
