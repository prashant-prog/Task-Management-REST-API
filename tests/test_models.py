from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User


@pytest.fixture
def db_session():
    """Provide a transactional session for testing models with cleanup."""
    session: Session = SessionLocal()
    yield session
    # Cleanup after test: clean users (cascades to tasks)
    session.rollback()
    session.query(Task).delete()
    session.query(User).delete()
    session.commit()
    session.close()


def test_create_user_and_task_relationship(db_session: Session) -> None:
    """Verify creating a user, assigning tasks, and loading relationships."""
    user = User(
        email="testowner@example.com",
        hashed_password="hashed_secret_string",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.email == "testowner@example.com"
    assert user.is_active is True
    assert user.created_at is not None

    # Create a task for this user
    task = Task(
        title="Complete backend milestone",
        description="Write models and migrations",
        status=TaskStatus.IN_PROGRESS,
        priority=TaskPriority.HIGH,
        due_date=datetime.now(UTC),
        user_id=user.id,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    # Verify task attributes and relationship back to owner
    assert task.id is not None
    assert task.owner.email == user.email
    assert task.status == TaskStatus.IN_PROGRESS
    assert task.priority == TaskPriority.HIGH

    # Verify user's tasks relationship
    db_session.refresh(user)
    assert len(user.tasks) == 1
    assert user.tasks[0].id == task.id


def test_user_email_unique_constraint(db_session: Session) -> None:
    """Verify that duplicate user emails violate the unique constraint."""
    user1 = User(
        email="duplicate@example.com",
        hashed_password="password1",
    )
    db_session.add(user1)
    db_session.commit()

    user2 = User(
        email="duplicate@example.com",
        hashed_password="password2",
    )
    db_session.add(user2)
    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_cascade_delete_user_removes_tasks(db_session: Session) -> None:
    """Verify that deleting a user automatically cascades and deletes their tasks."""
    user = User(
        email="cascade_test@example.com",
        hashed_password="password",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    task = Task(
        title="Task to be cascade deleted",
        user_id=user.id,
    )
    db_session.add(task)
    db_session.commit()
    task_id = task.id

    # Delete the user
    db_session.delete(user)
    db_session.commit()

    # Query for the task to confirm it was cascade deleted
    deleted_task = db_session.execute(
        select(Task).where(Task.id == task_id)
    ).scalar_one_or_none()
    assert deleted_task is None
