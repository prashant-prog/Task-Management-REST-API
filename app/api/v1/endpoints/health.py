from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.schemas.health import HealthCheckResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check operational status of API server and database.",
)
def health_check(
    db: Annotated[Session, Depends(get_db)],
) -> HealthCheckResponse:
    """Return application and database health information."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except SQLAlchemyError:
        db_status = "disconnected"

    return HealthCheckResponse(
        status="healthy" if db_status == "connected" else "degraded",
        app_name=settings.PROJECT_NAME,
        environment=settings.ENVIRONMENT,
        database=db_status,
    )
