from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

client = TestClient(app)


def test_root_endpoint() -> None:
    """Verify that root endpoint returns HTTP 200 and links to documentation."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == f"Welcome to {settings.PROJECT_NAME}"
    assert data["docs_url"] == "/docs"
    assert data["health_check"] == f"{settings.API_V1_STR}/health"


def test_health_check_endpoint() -> None:
    """Verify that health check reports healthy app and connected database."""
    response = client.get(f"{settings.API_V1_STR}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == settings.PROJECT_NAME
    assert data["environment"] == settings.ENVIRONMENT
    assert data["database"] == "connected"
