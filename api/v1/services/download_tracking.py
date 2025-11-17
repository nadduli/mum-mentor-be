from sqlalchemy.orm import Session
from fastapi import Request
from datetime import datetime
from api.v1.models.downloads import DownloadEvent
from api.v1.schemas.downloads import DownloadTrackRequest

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
    user_id: str | None = None,
    session_id: str | None = None,
):
    referrer = request.headers.get("referer") or request.headers.get("referrer")
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    device_type = _infer_device_type(user_agent)

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
        occurred_at=datetime.utcnow(),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_download_stats(
    db: Session,
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
    group_by: str = "download_type",
):
    from sqlalchemy import func
    query = db.query(getattr(DownloadEvent, group_by), func.count(DownloadEvent.id))
    if from_dt:
        query = query.filter(DownloadEvent.occurred_at >= from_dt)
    if to_dt:
        query = query.filter(DownloadEvent.occurred_at <= to_dt)
    query = query.group_by(getattr(DownloadEvent, group_by))
    rows = query.all()
    return [{group_by: r[0], "count": r[1]} for r in rows]
