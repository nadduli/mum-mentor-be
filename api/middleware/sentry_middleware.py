from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import sentry_sdk
from api.utils.logger import get_correlation_id


class SentryContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add custom context to Sentry events
    """
    
    async def dispatch(self, request: Request, call_next):
        # Add request context to Sentry
        with sentry_sdk.configure_scope() as scope:
            # Add user info if available
            if hasattr(request.state, 'user_id'):
                scope.set_user({
                    "id": str(request.state.user_id)
                })
            
            # Add correlation ID for tracing
            correlation_id = get_correlation_id()
            if correlation_id:
                scope.set_tag("correlation_id", correlation_id)
            
            # Add request metadata
            scope.set_context("request", {
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers),
                "query_params": dict(request.query_params),
            })
        
        response = await call_next(request)
        return response
