from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1.routes import app as api_v1_router
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(
    title="Mum Mentor AI (NORA) API",
    description="Backend API for Mum Mentor AI - A digital companion for mothers",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 routers
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
