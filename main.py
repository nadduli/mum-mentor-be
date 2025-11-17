from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1.routes import app as api_v1_router
from api.v1.routes.auth.auth_route import login_router
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

app.include_router(api_v1_router, prefix="/api/v1")

app.include_router(login_router, prefix="/api/v1")

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
