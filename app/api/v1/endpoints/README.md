# Route Handlers (`app/api/v1/endpoints/`)

This directory houses the route handler modules that implement the core HTTP operations of the API.

---

## 1. Directory Structure

```text
app/api/v1/endpoints/
├── __init__.py           # Package marker
├── auth.py               # Authentication endpoints (/register, /login, /me)
├── health.py             # Health check probe (/health)
├── tasks.py              # Task CRUD with query features (/tasks/)
└── README.md             # This documentation file
```

---

## 2. Endpoints Breakdown

### 1. [`health.py`](health.py) — Health Check & Readiness Probe
- **`GET /api/v1/health`**
  - **Auth:** Public
  - **Status Code:** `200 OK`
  - **Response Model:** `HealthCheckResponse`
  - **Description:** Injects `db: Annotated[Session, Depends(get_db)]` and executes `SELECT 1` on PostgreSQL. If successful, reports `"database": "connected"`. If database is down, reports `"database": "disconnected"`.

---

### 2. [`auth.py`](auth.py) — Authentication & Profile
- **`POST /api/v1/auth/register`**
  - **Auth:** Public
  - **Status Code:** `201 Created`
  - **Request Body:** `UserCreate` (`email: EmailStr`, `password: str` min 8 chars)
  - **Response Model:** `UserResponse`
  - **Description:** Checks for duplicate emails (returns `400 Bad Request`), hashes the password using Argon2, stores the user in PostgreSQL, and returns user details without the password.

- **`POST /api/v1/auth/login`**
  - **Auth:** Public (OAuth2 Password Grant)
  - **Status Code:** `200 OK`
  - **Request Body:** Form data (`username` = email, `password` = password)
  - **Response Model:** `Token` (`access_token`, `token_type: "bearer"`)
  - **Description:** Verifies password hash using Argon2. Generates signed JWT access token encoding `sub = user.id` and expiration (`exp`).

- **`GET /api/v1/auth/me`**
  - **Auth:** Required (`Bearer <token>`)
  - **Status Code:** `200 OK`
  - **Response Model:** `UserResponse`
  - **Description:** Injects `current_user: Annotated[User, Depends(get_current_active_user)]` and returns current user account information.

---

### 3. [`tasks.py`](tasks.py) — Task CRUD & Query Features
- **`POST /api/v1/tasks/`**
  - **Auth:** Required
  - **Status Code:** `201 Created`
  - **Request Body:** `TaskCreate` (`title`, `description`, `status`, `priority`, `due_date`)
  - **Response Model:** `TaskResponse`
  - **Description:** Creates a task strictly bound to `user_id = current_user.id`.

- **`GET /api/v1/tasks/`**
  - **Auth:** Required
  - **Status Code:** `200 OK`
  - **Query Parameters:**
    - `status: TaskStatus | None` (filter by `pending`, `in_progress`, `completed`)
    - `priority: TaskPriority | None` (filter by `low`, `medium`, `high`)
    - `sort_by: TaskSortField` (`created_at` or `due_date`, default `created_at`)
    - `order: SortOrder` (`asc` or `desc`, default `desc`)
    - `limit: int` (1 to 100, default `10`)
    - `offset: int` (`>= 0`, default `0`)
  - **Response Model:** `PaginatedTaskResponse` (`items`, `total`, `limit`, `offset`)
  - **Description:** Retrieves paginated, sorted, and filtered tasks belonging strictly to the current user. Sorting by `due_date` applies `.nulls_last()`.

- **`GET /api/v1/tasks/{task_id}`**
  - **Auth:** Required
  - **Status Code:** `200 OK`
  - **Response Model:** `TaskResponse`
  - **Description:** Retrieves single task matching `Task.id == task_id` and `Task.user_id == current_user.id`. Returns `404 Not Found` if nonexistent or owned by another user.

- **`PATCH /api/v1/tasks/{task_id}`**
  - **Auth:** Required
  - **Status Code:** `200 OK`
  - **Request Body:** `TaskUpdate` (all fields optional)
  - **Response Model:** `TaskResponse`
  - **Description:** Partially updates specified fields (`exclude_unset=True`) of a task owned by the current user. Returns `404 Not Found` if unauthorized.

- **`DELETE /api/v1/tasks/{task_id}`**
  - **Auth:** Required
  - **Status Code:** `204 No Content`
  - **Description:** Deletes task owned by the current user. Returns `404 Not Found` if unauthorized.
