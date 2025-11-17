from fastapi import FastAPI
from api.v1.routes import app as v1_app

app = FastAPI(
    title="Mum Mentor API",
    version="1.0.0",
    description="API for Mum Mentor platform"
)

app.include_router(v1_app, prefix="/api/v1")


@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
