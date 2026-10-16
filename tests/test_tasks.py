import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.main import app
from app.models.task import Task
from app.models.user import User

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_database():
    """Clean up database tables before and after each test."""
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


def get_auth_token_for_user(email: str, password: str = "password123") -> str:
    """Helper fixture to register, log in, and return a JWT access token."""
    client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"email": email, "password": password},
    )
    login_res = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": email, "password": password},
    )
    return login_res.json()["access_token"]


def test_create_task_authenticated() -> None:
    """Verify that an authenticated user can create a task."""
    token = get_auth_token_for_user("owner@example.com")
    response = client.post(
        f"{settings.API_V1_STR}/tasks/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Build CRUD endpoints",
            "description": "Complete Milestone 6",
            "priority": "high",
            "status": "in_progress",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Build CRUD endpoints"
    assert data["description"] == "Complete Milestone 6"
    assert data["priority"] == "high"
    assert data["status"] == "in_progress"
    assert "id" in data
    assert "user_id" in data


def test_create_task_unauthenticated_fails() -> None:
    """Verify that creating a task without token returns HTTP 401."""
    response = client.post(
        f"{settings.API_V1_STR}/tasks/",
        json={"title": "Unauthenticated task"},
    )
    assert response.status_code == 401


def test_get_single_task() -> None:
    """Verify that the owner can retrieve their own task by ID."""
    token = get_auth_token_for_user("user1@example.com")
    create_res = client.post(
        f"{settings.API_V1_STR}/tasks/",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Read SQLAlchemy documentation"},
    )
    task_id = create_res.json()["id"]

    get_res = client.get(
        f"{settings.API_V1_STR}/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Read SQLAlchemy documentation"


def test_list_tasks_isolation() -> None:
    """Verify that users can list only their own tasks."""
    token_a = get_auth_token_for_user("user_a@example.com")
    token_b = get_auth_token_for_user("user_b@example.com")

    # User A creates 2 tasks
    client.post(
        f"{settings.API_V1_STR}/tasks/",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"title": "User A - Task 1"},
    )
    client.post(
        f"{settings.API_V1_STR}/tasks/",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"title": "User A - Task 2"},
    )

    # User B creates 1 task
    client.post(
        f"{settings.API_V1_STR}/tasks/",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"title": "User B - Task 1"},
    )

    # Verify User A only sees their 2 tasks
    res_a = client.get(
        f"{settings.API_V1_STR}/tasks/",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res_a.status_code == 200
    tasks_a = res_a.json()
    assert len(tasks_a) == 2
    assert all("User A" in t["title"] for t in tasks_a)

    # Verify User B only sees their 1 task
    res_b = client.get(
        f"{settings.API_V1_STR}/tasks/",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_b.status_code == 200
    tasks_b = res_b.json()
    assert len(tasks_b) == 1
    assert tasks_b[0]["title"] == "User B - Task 1"


def test_update_task() -> None:
    """Verify that a task can be partially updated."""
    token = get_auth_token_for_user("updater@example.com")
    create_res = client.post(
        f"{settings.API_V1_STR}/tasks/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Draft blog post",
            "status": "pending",
            "priority": "low",
        },
    )
    task_id = create_res.json()["id"]

    # Partially update status and priority
    update_res = client.patch(
        f"{settings.API_V1_STR}/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "completed", "priority": "high"},
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["status"] == "completed"
    assert updated_data["priority"] == "high"
    assert updated_data["title"] == "Draft blog post"


def test_delete_task() -> None:
    """Verify that a task can be deleted by its owner."""
    token = get_auth_token_for_user("deleter@example.com")
    create_res = client.post(
        f"{settings.API_V1_STR}/tasks/",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Temporary task"},
    )
    task_id = create_res.json()["id"]

    delete_res = client.delete(
        f"{settings.API_V1_STR}/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_res.status_code == 204

    # Verify task no longer exists
    get_res = client.get(
        f"{settings.API_V1_STR}/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_res.status_code == 404


def test_ownership_enforcement_cannot_view_others_task() -> None:
    """Verify that User B cannot retrieve User A's task (returns 404)."""
    token_a = get_auth_token_for_user("alice@example.com")
    token_b = get_auth_token_for_user("bob@example.com")

    # Alice creates a task
    create_res = client.post(
        f"{settings.API_V1_STR}/tasks/",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"title": "Alice's Secret Task"},
    )
    task_id = create_res.json()["id"]

    # Bob attempts to get Alice's task
    get_res = client.get(
        f"{settings.API_V1_STR}/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert get_res.status_code == 404
    assert get_res.json()["detail"] == "Task not found"


def test_ownership_enforcement_cannot_update_others_task() -> None:
    """Verify that User B cannot update User A's task (returns 404)."""
    token_a = get_auth_token_for_user("alice2@example.com")
    token_b = get_auth_token_for_user("bob2@example.com")

    # Alice creates a task
    create_res = client.post(
        f"{settings.API_V1_STR}/tasks/",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"title": "Original Title"},
    )
    task_id = create_res.json()["id"]

    # Bob attempts to update Alice's task
    patch_res = client.patch(
        f"{settings.API_V1_STR}/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"title": "Hacked Title"},
    )
    assert patch_res.status_code == 404

    # Confirm task title remains unchanged
    alice_res = client.get(
        f"{settings.API_V1_STR}/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert alice_res.json()["title"] == "Original Title"


def test_ownership_enforcement_cannot_delete_others_task() -> None:
    """Verify that User B cannot delete User A's task (returns 404)."""
    token_a = get_auth_token_for_user("alice3@example.com")
    token_b = get_auth_token_for_user("bob3@example.com")

    # Alice creates a task
    create_res = client.post(
        f"{settings.API_V1_STR}/tasks/",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"title": "Protected Task"},
    )
    task_id = create_res.json()["id"]

    # Bob attempts to delete Alice's task
    delete_res = client.delete(
        f"{settings.API_V1_STR}/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert delete_res.status_code == 404

    # Confirm Alice's task still exists
    alice_res = client.get(
        f"{settings.API_V1_STR}/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert alice_res.status_code == 200
