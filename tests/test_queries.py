from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.core.config import settings


def get_token(client: TestClient, email: str = "queryuser@example.com") -> str:
    """Helper to register and login a test user."""
    client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"email": email, "password": "password123"},
    )
    login_res = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": email, "password": "password123"},
    )
    return login_res.json()["access_token"]


def seed_tasks(client: TestClient, token: str) -> None:
    """Seed a variety of tasks for querying tests."""
    headers = {"Authorization": f"Bearer {token}"}
    now = datetime.now(UTC)

    tasks_data = [
        {
            "title": "Task 1 - Low/Pending",
            "status": "pending",
            "priority": "low",
            "due_date": (now + timedelta(days=5)).isoformat(),
        },
        {
            "title": "Task 2 - High/In Progress",
            "status": "in_progress",
            "priority": "high",
            "due_date": (now + timedelta(days=1)).isoformat(),
        },
        {
            "title": "Task 3 - High/Completed",
            "status": "completed",
            "priority": "high",
            "due_date": (now + timedelta(days=2)).isoformat(),
        },
        {
            "title": "Task 4 - Medium/Pending (No Due Date)",
            "status": "pending",
            "priority": "medium",
            "due_date": None,
        },
        {
            "title": "Task 5 - Low/Completed",
            "status": "completed",
            "priority": "low",
            "due_date": (now + timedelta(days=10)).isoformat(),
        },
    ]

    for item in tasks_data:
        res = client.post(
            f"{settings.API_V1_STR}/tasks/",
            headers=headers,
            json=item,
        )
        assert res.status_code == 201


def test_filter_by_status(client: TestClient) -> None:
    """Verify filtering tasks by status."""
    token = get_token(client, "filter_status@example.com")
    seed_tasks(client, token)

    res = client.get(
        f"{settings.API_V1_STR}/tasks/?status=pending",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    assert all(t["status"] == "pending" for t in data["items"])


def test_filter_by_priority(client: TestClient) -> None:
    """Verify filtering tasks by priority."""
    token = get_token(client, "filter_priority@example.com")
    seed_tasks(client, token)

    res = client.get(
        f"{settings.API_V1_STR}/tasks/?priority=high",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    assert all(t["priority"] == "high" for t in data["items"])


def test_combined_filters(client: TestClient) -> None:
    """Verify combining status and priority filters."""
    token = get_token(client, "combined@example.com")
    seed_tasks(client, token)

    res = client.get(
        f"{settings.API_V1_STR}/tasks/?status=completed&priority=high",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Task 3 - High/Completed"


def test_sorting_by_due_date_predictable_nulls(client: TestClient) -> None:
    """Verify sorting by due_date ascending places null due dates at the end."""
    token = get_token(client, "sort_due@example.com")
    seed_tasks(client, token)

    res = client.get(
        f"{settings.API_V1_STR}/tasks/?sort_by=due_date&order=asc",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    items = res.json()["items"]
    # Task with null due date must be placed last
    assert items[-1]["due_date"] is None
    # First item must have earliest due date (1 day out -> Task 2)
    assert items[0]["title"] == "Task 2 - High/In Progress"


def test_pagination_limit_and_offset(client: TestClient) -> None:
    """Verify pagination limit and offset slices correctly."""
    token = get_token(client, "pagination@example.com")
    seed_tasks(client, token)

    # Fetch page 1 (limit 2, offset 0)
    page1 = client.get(
        f"{settings.API_V1_STR}/tasks/?limit=2&offset=0",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    assert len(page1["items"]) == 2
    assert page1["total"] == 5
    assert page1["limit"] == 2
    assert page1["offset"] == 0

    # Fetch page 2 (limit 2, offset 2)
    page2 = client.get(
        f"{settings.API_V1_STR}/tasks/?limit=2&offset=2",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    assert len(page2["items"]) == 2
    assert page2["total"] == 5
    assert page2["offset"] == 2

    # Verify no overlap between page 1 and page 2
    page1_ids = [t["id"] for t in page1["items"]]
    page2_ids = [t["id"] for t in page2["items"]]
    assert set(page1_ids).isdisjoint(set(page2_ids))


def test_invalid_query_parameters_validation(client: TestClient) -> None:
    """Verify that invalid query parameters return HTTP 422."""
    token = get_token(client, "invalid_queries@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Invalid status
    res1 = client.get(
        f"{settings.API_V1_STR}/tasks/?status=invalid_status",
        headers=headers,
    )
    assert res1.status_code == 422

    # Invalid priority
    res2 = client.get(
        f"{settings.API_V1_STR}/tasks/?priority=urgent",
        headers=headers,
    )
    assert res2.status_code == 422

    # Invalid sort field
    res3 = client.get(
        f"{settings.API_V1_STR}/tasks/?sort_by=hacked_field",
        headers=headers,
    )
    assert res3.status_code == 422

    # Invalid order direction
    res4 = client.get(
        f"{settings.API_V1_STR}/tasks/?order=sideways",
        headers=headers,
    )
    assert res4.status_code == 422

    # Limit exceeded (max 100)
    res5 = client.get(
        f"{settings.API_V1_STR}/tasks/?limit=500",
        headers=headers,
    )
    assert res5.status_code == 422

    # Negative offset
    res6 = client.get(
        f"{settings.API_V1_STR}/tasks/?offset=-5",
        headers=headers,
    )
    assert res6.status_code == 422


def test_deterministic_pagination_with_colliding_sort_values(
    client: TestClient,
) -> None:
    """Verify deterministic pagination ordering when tasks share identical sort values.

    Without a deterministic tie-breaker (like Task.id), database engines can return
    arbitrary orderings across LIMIT/OFFSET slices when sort keys collide.
    """
    token = get_token(client, "deterministic_sort@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    identical_due_date = (datetime.now(UTC) + timedelta(days=3)).isoformat()

    created_ids: list[int] = []
    for i in range(6):
        res = client.post(
            f"{settings.API_V1_STR}/tasks/",
            headers=headers,
            json={
                "title": f"Colliding Task {i}",
                "due_date": identical_due_date,
            },
        )
        assert res.status_code == 201
        created_ids.append(res.json()["id"])

    # 1. Test ASC sort with collision: tie-breaker should sort Task.id ASC
    p1_asc = client.get(
        f"{settings.API_V1_STR}/tasks/?sort_by=due_date&order=asc&limit=3&offset=0",
        headers=headers,
    ).json()
    p2_asc = client.get(
        f"{settings.API_V1_STR}/tasks/?sort_by=due_date&order=asc&limit=3&offset=3",
        headers=headers,
    ).json()

    p1_asc_ids = [t["id"] for t in p1_asc["items"]]
    p2_asc_ids = [t["id"] for t in p2_asc["items"]]

    # Verify each page is strictly ascending by ID
    assert p1_asc_ids == sorted(p1_asc_ids)
    assert p2_asc_ids == sorted(p2_asc_ids)
    # Verify no page drift / overlap
    assert set(p1_asc_ids).isdisjoint(set(p2_asc_ids))
    assert p1_asc_ids + p2_asc_ids == sorted(created_ids)

    # 2. Test DESC sort with collision: tie-breaker should sort Task.id DESC
    p1_desc = client.get(
        f"{settings.API_V1_STR}/tasks/?sort_by=due_date&order=desc&limit=3&offset=0",
        headers=headers,
    ).json()
    p2_desc = client.get(
        f"{settings.API_V1_STR}/tasks/?sort_by=due_date&order=desc&limit=3&offset=3",
        headers=headers,
    ).json()

    p1_desc_ids = [t["id"] for t in p1_desc["items"]]
    p2_desc_ids = [t["id"] for t in p2_desc["items"]]

    # Verify each page is strictly descending by ID
    assert p1_desc_ids == sorted(p1_desc_ids, reverse=True)
    assert p2_desc_ids == sorted(p2_desc_ids, reverse=True)
    # Verify no page drift / overlap
    assert set(p1_desc_ids).isdisjoint(set(p2_desc_ids))
    assert p1_desc_ids + p2_desc_ids == sorted(created_ids, reverse=True)

