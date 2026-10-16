from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.task import TaskPriority, TaskStatus


class TaskBase(BaseModel):
    """Base schema containing shared task attributes."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Title or summary of the task",
    )
    description: str | None = Field(
        default=None,
        description="Optional detailed description of the task",
    )
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        description="Current state of completion",
    )
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM,
        description="Urgency/importance priority level",
    )
    due_date: datetime | None = Field(
        default=None,
        description="Optional deadline in UTC",
    )


class TaskCreate(TaskBase):
    """Schema for creating a new task.

    Notice: user_id is NOT included here.
    The owner is always inferred securely from the authenticated session.
    """


class TaskUpdate(BaseModel):
    """Schema for partially updating an existing task.

    All fields are optional; only provided fields will be updated.
    """

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Updated title",
    )
    description: str | None = Field(
        default=None,
        description="Updated description",
    )
    status: TaskStatus | None = Field(
        default=None,
        description="Updated status",
    )
    priority: TaskPriority | None = Field(
        default=None,
        description="Updated priority",
    )
    due_date: datetime | None = Field(
        default=None,
        description="Updated due date in UTC",
    )


class TaskResponse(TaskBase):
    """Schema for task data returned in API responses."""

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
