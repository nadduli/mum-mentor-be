from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.deps import get_current_user
from api.v1.models.user.user import User
from api.v1.schemas.delete_account import AccountDeletionRequest, AccountDeletionResponse
from api.v1.services.delete_account import AccountService
from api.v1.services.email_services import send_email
from api.utils.responses import success_response, fail_response
from api.utils.logger import logger
from datetime import datetime, timezone

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.delete(
    "/delete",
    status_code=status.HTTP_200_OK,
    summary="Delete user account",
    description="Permanently delete user account and all associated data. Requires password confirmation."
)
async def delete_account(
    request: AccountDeletionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete user account permanently.
    
    - **password**: Current password for confirmation
    - **confirmation_phrase**: Must be exactly "DELETE MY ACCOUNT"
    
    This action cannot be undone. All user data will be permanently removed.
    """
    logger.info("Account deletion request for user: %s", current_user.email)
    
    # Check if account is already deleted
    if current_user.is_deleted:
        logger.warning("Attempt to delete already deleted account: %s", current_user.id)
        return fail_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Account already deleted"
        )

    # Delete account
    success, error = AccountService.delete_user_account(
        db, str(current_user.id), request.password
    )
    
    if not success:
        logger.warning(
            "Account deletion failed for user %s: %s",
            current_user.email,
            error
        )
        return fail_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=error
        )

    # Send confirmation email (optional)
    try:
        if current_user.email and not current_user.email.startswith("deleted_"):
            subject = "Account Deletion Confirmation"
            body = f"""Hi {current_user.full_name},

Your account and all associated data have been permanently deleted from our systems.

If this was a mistake or you change your mind, please contact our support team immediately.

We're sorry to see you go!

Best regards,
The Nora Team"""
            
            await send_email(current_user.email, subject, body)
            logger.info("Deletion confirmation email sent to: %s", current_user.email)
    except Exception as email_error:
        logger.error(
            "Failed to send deletion confirmation email to %s: %s",
            current_user.email,
            str(email_error),
            exc_info=True
        )
        # Don't fail the request if email fails

    logger.info("Account successfully deleted for user: %s", current_user.email)
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Account and all associated data have been permanently deleted",
        data={
            "deletion_time": datetime.now(timezone.utc).isoformat()
        }
    )