from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.main import app
from app.models.task import Task
from app.models.user import User

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_database():
    """Clean up users and tasks tables before and after each test."""
    session: Session = SessionLocal()
    session.query(Task).delete()
    session.query(User).delete()
    session.commit()
    yield
    session.rollback()
    session.query(Task).delete()
    session.query(User).delete()
    session.commit()
    session.close()


def test_register_user_success() -> None:
    """Verify that a user can register successfully with valid credentials."""
    response = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"email": "newuser@example.com", "password": "securepassword123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["is_active"] is True
    assert "id" in data
    # Ensure sensitive fields like password or hashed_password are NEVER returned
    assert "password" not in data
    assert "hashed_password" not in data


def test_register_duplicate_email_fails() -> None:
    """Verify that registering with an already existing email returns HTTP 400."""
    payload = {"email": "duplicate@example.com", "password": "password123"}
    # First registration succeeds
    response1 = client.post(f"{settings.API_V1_STR}/auth/register", json=payload)
    assert response1.status_code == 201

    # Second registration with same email fails
    response2 = client.post(f"{settings.API_V1_STR}/auth/register", json=payload)
    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"]


def test_register_validation_error_short_password() -> None:
    """Verify that passwords shorter than 8 characters fail with HTTP 422."""
    response = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"email": "short@example.com", "password": "short"},
    )
    assert response.status_code == 422


def test_login_success() -> None:
    """Verify that a registered user can log in and receive a valid JWT token."""
    # Register user first
    client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"email": "loginuser@example.com", "password": "securepassword123"},
    )

    # Log in using OAuth2 standard form data
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": "loginuser@example.com", "password": "securepassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password_fails() -> None:
    """Verify that login fails with HTTP 401 when password is wrong."""
    client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"email": "wrongpw@example.com", "password": "correctpassword123"},
    )

    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": "wrongpw@example.com", "password": "wrongpassword123"},
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_get_current_user_me_endpoint() -> None:
    """Verify protected endpoint returns user details with valid Bearer token."""
    reg_response = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"email": "me@example.com", "password": "mypassword123"},
    )
    user_id = reg_response.json()["id"]

    # Login to get token
    login_response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": "me@example.com", "password": "mypassword123"},
    )
    token = login_response.json()["access_token"]

    # Access protected /auth/me
    me_response = client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["id"] == user_id
    assert me_data["email"] == "me@example.com"


def test_protected_route_missing_token_fails() -> None:
    """Verify that accessing protected route without a token returns HTTP 401."""
    response = client.get(f"{settings.API_V1_STR}/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_protected_route_invalid_token_fails() -> None:
    """Verify that accessing protected route with a tampered token returns HTTP 401."""
    response = client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": "Bearer invalid.fake.token"},
    )
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]


def test_protected_route_expired_token_fails() -> None:
    """Verify that accessing protected route with an expired token returns HTTP 401."""
    # Register user
    reg_response = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"email": "expired@example.com", "password": "password123"},
    )
    user_id = reg_response.json()["id"]

    # Create an already-expired token
    expired_token = create_access_token(
        subject=user_id,
        expires_delta=timedelta(minutes=-10),
    )

    response = client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    assert "Token has expired" in response.json()["detail"]
