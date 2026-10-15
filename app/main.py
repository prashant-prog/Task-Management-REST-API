from fastapi import FastAPI, status

from app.api.v1.api import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    description="Task Management REST API with FastAPI, PostgreSQL, and SQLAlchemy.",
    version="1.0.0",
)

# Include v1 API endpoints
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get(
    "/",
    status_code=status.HTTP_200_OK,
    tags=["Root"],
    summary="Root Endpoint",
)
def root() -> dict[str, str]:
    """Provide a friendly entry point and links to API documentation."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "docs_url": "/docs",
        "health_check": f"{settings.API_V1_STR}/health",
    }
