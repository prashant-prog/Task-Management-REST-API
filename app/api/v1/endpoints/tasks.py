from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User
from app.schemas.task import (
    PaginatedTaskResponse,
    SortOrder,
    TaskCreate,
    TaskResponse,
    TaskSortField,
    TaskUpdate,
)

router = APIRouter()


@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Task",
    description="Create a new task owned by the authenticated user.",
)
def create_task(
    task_in: TaskCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Task:
    """Create a new task.

    Task ownership is automatically bound to current_user.id.
    """
    task = Task(
        **task_in.model_dump(),
        user_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get(
    "/",
    response_model=PaginatedTaskResponse,
    status_code=status.HTTP_200_OK,
    summary="List Tasks",
    description=(
        "Retrieve tasks owned by the authenticated user with filtering, "
        "sorting, and pagination."
    ),
)
def list_tasks(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    status: Annotated[
        TaskStatus | None,
        Query(description="Filter tasks by status"),
    ] = None,
    priority: Annotated[
        TaskPriority | None,
        Query(description="Filter tasks by priority"),
    ] = None,
    sort_by: Annotated[
        TaskSortField,
        Query(description="Sort field ('created_at' or 'due_date')"),
    ] = TaskSortField.CREATED_AT,
    order: Annotated[
        SortOrder,
        Query(description="Sort direction ('asc' or 'desc')"),
    ] = SortOrder.DESC,
    limit: Annotated[
        int,
        Query(ge=1, le=100, description="Max items per page (1-100)"),
    ] = 10,
    offset: Annotated[
        int,
        Query(ge=0, description="Number of items to skip"),
    ] = 0,
) -> PaginatedTaskResponse:
    """Return paginated, filtered, and sorted tasks for the current user."""
    # 1. Base query filtered strictly by authenticated user
    base_query = select(Task).where(Task.user_id == current_user.id)

    # 2. Dynamic filters
    if status is not None:
        base_query = base_query.where(Task.status == status)
    if priority is not None:
        base_query = base_query.where(Task.priority == priority)

    # 3. Compute total matching records count before pagination
    count_query = select(func.count()).select_from(base_query.subquery())
    total = db.execute(count_query).scalar_one()

    # 4. Sorting with predictable NULL handling and deterministic tie-breaker
    sort_column = getattr(Task, sort_by.value)
    if order == SortOrder.ASC:
        order_expr = sort_column.asc().nulls_last()
        tie_breaker = Task.id.asc()
    else:
        order_expr = sort_column.desc().nulls_last()
        tie_breaker = Task.id.desc()

    # 5. Apply sorting, limit, and offset
    paginated_query = (
        base_query.order_by(order_expr, tie_breaker).limit(limit).offset(offset)
    )
    tasks = list(db.execute(paginated_query).scalars().all())

    return PaginatedTaskResponse(
        items=tasks,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Single Task",
    description="Retrieve a single task by ID. Only the task owner can access it.",
)
def get_task(
    task_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Task:
    """Retrieve a task owned by the current user."""
    query = select(Task).where(
        Task.id == task_id,
        Task.user_id == current_user.id,
    )
    task = db.execute(query).scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return task


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Task",
    description="Partially update an existing task owned by the authenticated user.",
)
def update_task(
    task_id: int,
    task_in: TaskUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Task:
    """Update fields of an existing task owned by the current user."""
    query = select(Task).where(
        Task.id == task_id,
        Task.user_id == current_user.id,
    )
    task = db.execute(query).scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Apply only explicitly provided update values
    update_data = task_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Task",
    description="Delete a task by ID. Only the task owner can delete it.",
)
def delete_task(
    task_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Delete a task owned by the current user."""
    query = select(Task).where(
        Task.id == task_id,
        Task.user_id == current_user.id,
    )
    task = db.execute(query).scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    db.delete(task)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
