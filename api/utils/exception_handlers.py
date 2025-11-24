from fastapi import Request, status
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.responses import JSONResponse

from api.utils.responses import fail_response


def request_validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Override default Pydantic/FastAPI validation errors and make it conform to project-defined fail_response format.
    """
    return fail_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Invalid request data",
        context={"errors": exc.errors()}
    )

def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    """
    Override default HTTPException responses (e.g., raise HTTPException(...)).
    """
    return fail_response(
        status_code=exc.status_code,
        message=exc.detail,
        context={}
    )