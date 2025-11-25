import os
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from dotenv import load_dotenv

load_dotenv()


def init_sentry():
    """Initialize Sentry SDK with FastAPI integration"""
    
    sentry_dsn = os.getenv("SENTRY_DSN")
    environment = os.getenv("SENTRY_ENVIRONMENT", "development")
    traces_sample_rate = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "1.0"))
    profiles_sample_rate = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "1.0"))
    
    # Only initialize if DSN is provided
    if not sentry_dsn:
        print("⚠️  Sentry DSN not found. Sentry monitoring disabled.")
        return
    
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=environment,
        
        # Performance Monitoring
        traces_sample_rate=traces_sample_rate,
        profiles_sample_rate=profiles_sample_rate,
        
        # Integrations
        integrations=[
            FastApiIntegration(
                transaction_style="endpoint",  # Group by endpoint
                failed_request_status_codes=[500, 501, 502, 503, 504, 505],
            ),
            StarletteIntegration(
                transaction_style="endpoint",
                failed_request_status_codes=[500, 501, 502, 503, 504, 505],
            ),
            SqlalchemyIntegration(),
            LoggingIntegration(
                level=None,  # Capture all log levels
                event_level=None  # Send logs as breadcrumbs
            ),
        ],
        
        # Release tracking (optional)
        release=os.getenv("SENTRY_RELEASE", "mum-mentor-api@1.0.0"),
        
        # Filter out health check endpoints
        before_send=before_send_filter,
        
        # Additional options
        attach_stacktrace=True,
        send_default_pii=False,  # Don't send personally identifiable info
        max_breadcrumbs=50,
        debug=environment == "development",
    )
    
    print(f"✅ Sentry initialized for environment: {environment}")


def before_send_filter(event, hint):
    """Filter out events we don't want to send to Sentry"""
    
    # Don't send health check endpoints
    if event.get("request", {}).get("url", "").endswith(("/health", "/", "/docs")):
        return None
    
    # Don't send 404 errors
    if event.get("contexts", {}).get("response", {}).get("status_code") == 404:
        return None
    
    # Add custom tags
    event.setdefault("tags", {})
    event["tags"]["service"] = "mum-mentor-api"
    
    return event


def capture_custom_error(error, context=None):
    """
    Manually capture errors with additional context
    
    Args:
        error: The exception to capture
        context: Dict of additional context to attach
    """
    with sentry_sdk.push_scope() as scope:
        if context:
            for key, value in context.items():
                scope.set_context(key, value)
        
        sentry_sdk.capture_exception(error)
