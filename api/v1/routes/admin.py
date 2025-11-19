import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import Any

from api.v1.schemas.admin import AdminCreate, AdminOut
from api.db.database import get_db
from api.v1.services.admin_service import create_admin
from api.v1.routes.auth.deps import require_super_admin
from api.utils.responses import success_response, fail_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_admin(
    payload: AdminCreate,
    db: Session = Depends(get_db),
    _super_admin = Depends(require_super_admin),  # ensures only super_admin can call
) -> Any:
    """
    Register a new admin. Only callable by an authenticated super_admin.
    """
    try:
        _, meta = create_admin(db=db, admin_in=payload)
        return success_response(
            status_code=status.HTTP_201_CREATED,
            message=meta.get("message", "Admin created"),
            data={"admin": meta.get("user")}
        )
    except ValueError as e:
        return fail_response(status_code=status.HTTP_400_BAD_REQUEST, message=str(e))
    except Exception as e:
        # Unexpected error
        logger.exception("Unexpected error in register_admin")
        return fail_response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, message="Internal Server Error")