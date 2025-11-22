from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from api.utils.responses import validation_error_response
from api.v1.routes import app as api_v1_router

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(
    title="Mum Mentor AI (NORA) API",
    description="Backend API for Mum Mentor AI - A digital companion for mothers",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/api/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    formatted_errors = {}

    for err in exc.errors():
        field = err["loc"][-1]
        message = err["msg"]

        if field not in formatted_errors:
            formatted_errors[field] = []
        formatted_errors[field].append(message)

    return validation_error_response(formatted_errors)

app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/")
async def read_root():
    return {
        "message": "Welcome to Mum Mentor AI (NORA) API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
