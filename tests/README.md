# Automated Testing Suite & Test Architecture

This directory contains the automated test suite for the **Task Management REST API**, built using **Pytest**, **FastAPI TestClient (HTTPX)**, and **SQLAlchemy 2.0**.

The test suite covers unit and integration scenarios across all layers of the application: database connectivity, ORM models, authentication, security/JWT handling, authorization (IDOR protection), CRUD operations, and advanced querying.

---

## 1. Testing Philosophy & Architecture

```
                          ┌────────────────────────┐
                          │     pytest session     │
                          └───────────┬────────────┘
                                      │
              ┌───────────────────────┴───────────────────────┐
              ▼                                               ▼
   ┌───────────────────────┐                       ┌───────────────────────┐
   │  tests/conftest.py    │                       │   FastAPI App Entry   │
   │  - Connects to:       │                       │   (app/main.py)       │
   │    task_test_db       │                       └──────────┬────────────┘
   │  - Creates schema     │                                  │
   │  - dependency_override│                                  │
   └──────────┬────────────┘                                  │
              │                                               │
              ▼                                               │
   ┌────────────────────────────────────────────────────────┐ │
   │                TestClient (HTTP Client)                │◀┘
   │  Overrides get_db ──▶ Uses test_engine / task_test_db  │
   └────────────────────────────────────────────────────────┘
```

### Key Principles

1. **Strict Database Isolation:**
   - Automated tests **never** execute against the development database (`task_db`).
   - All tests run against a dedicated test database: `task_test_db`.
   - Running `pytest` will never delete or mutate your local development accounts or data.
2. **Dependency Injection Overrides (`app.dependency_overrides`):**
   - The application uses `Depends(get_db)` for database access.
   - During testing, `conftest.py` transparently replaces `get_db` with an isolated test session connected to `task_test_db`.
3. **Clean Slate Teardown:**
   - Every individual test receives an isolated transactional session (`db_session`).
   - At the end of each test, all database tables are purged in reverse topological order (foreign key safe) so subsequent tests run in a completely deterministic state.

---

## 2. Test Files Directory Structure

```text
tests/
├── conftest.py          # Centralized test configuration, fixtures, and DB overrides
├── test_database.py     # Database engine connectivity and session lifecycle tests
├── test_health.py       # Root welcome endpoint and DB health check probe tests
├── test_models.py       # SQLAlchemy ORM model relationships, constraints, and cascades
├── test_auth.py         # Registration, Argon2 hashing, login, and JWT token validation
├── test_tasks.py        # Task CRUD endpoints and strict ownership/IDOR authorization
├── test_queries.py      # Filtering, sorting, nulls handling, pagination, and validation
└── README.md            # This documentation file
```

---

## 3. Detailed File-by-File Breakdown

### 1. [`tests/conftest.py`](conftest.py) — Test Configuration & Fixtures
The backbone of the testing infrastructure. Pytest discovers fixtures defined here automatically across all test files.

- **`test_engine` & `TestingSessionLocal`:** Creates an engine instance bound to `settings.TEST_DATABASE_URL` (`task_test_db`).
- **`setup_test_database` (`scope="session"`):**
  - Runs once before any tests start: calls `Base.metadata.create_all(bind=test_engine)` to provision all tables and indexes.
  - Runs once after all tests finish: calls `Base.metadata.drop_all(bind=test_engine)` for clean teardown.
- **`db_session` (`scope="function"`):**
  - Yields a fresh SQLAlchemy `Session` for each test function.
  - Automatically executes `session.rollback()` and cleans all table rows upon test completion.
- **`client` (`scope="function"`):**
  - Configures `app.dependency_overrides[get_db]` to route all HTTP requests through the active test session.
  - Yields a FastAPI `TestClient` instance.
  - Clears `app.dependency_overrides` in the fixture teardown to prevent state pollution.

---

### 2. [`tests/test_database.py`](test_database.py) — Database Connectivity & Lifecycle
Verifies low-level SQLAlchemy engine operations and session management:

| Test Function | What It Validates |
| :--- | :--- |
| `test_database_engine_connection` | Confirms the engine can execute raw SQL (`SELECT 1`) on PostgreSQL and return scalar results. |
| `test_session_lifecycle` | Validates the `get_db()` generator lifecycle: proves that `yield db` provides an active session, executes queries, and the `finally: db.close()` block is guaranteed to terminate transactions and release connections. |

---

### 3. [`tests/test_health.py`](test_health.py) — Service Readiness Probes
Tests the public health and entry endpoints:

| Test Function | What It Validates |
| :--- | :--- |
| `test_root_endpoint` | Verifies `GET /` returns `HTTP 200 OK` with welcome metadata and links to OpenAPI documentation. |
| `test_health_check_endpoint` | Verifies `GET /api/v1/health` executes a live DB ping (`SELECT 1`) and returns `"status": "healthy"`, `"database": "connected"`. |

---

### 4. [`tests/test_models.py`](test_models.py) — ORM Relationships & Data Integrity
Tests database constraints and relational behavior directly at the SQLAlchemy level:

| Test Function | What It Validates |
| :--- | :--- |
| `test_create_user_and_task_relationship` | Verifies 1-to-many relationship: creating a `User`, assigning a `Task`, and verifying bidirectional ORM access (`task.owner` and `user.tasks`). |
| `test_user_email_unique_constraint` | Confirms inserting duplicate emails raises `sqlalchemy.exc.IntegrityError` and rolls back. |
| `test_cascade_delete_user_removes_tasks` | Tests both database-level (`ondelete="CASCADE"`) and ORM-level (`cascade="all, delete-orphan"`) cascading deletes: deleting a user automatically removes all their owned tasks. |

---

### 5. [`tests/test_auth.py`](test_auth.py) — Authentication & JWT Security
Tests user registration, Argon2 password hashing, and token validation:

| Test Function | What It Validates |
| :--- | :--- |
| `test_register_user_success` | Verifies `POST /auth/register` creates user with `HTTP 201 Created`. Confirms password and hash are **never** returned in the response schema. |
| `test_register_duplicate_email_fails` | Confirms registering an existing email returns `HTTP 400 Bad Request`. |
| `test_register_validation_error_short_password` | Tests Pydantic input validation: passwords < 8 characters fail with `HTTP 422 Unprocessable Entity`. |
| `test_login_success` | Tests OAuth2 password flow: authenticates credentials and returns signed JWT access token (`token_type: "bearer"`). |
| `test_login_invalid_password_fails` | Confirms wrong passwords return `HTTP 401 Unauthorized` ("Incorrect email or password"). |
| `test_get_current_user_me_endpoint` | Confirms authenticated requests with `Authorization: Bearer <token>` access `GET /auth/me` and receive user details. |
| `test_protected_route_missing_token_fails` | Accessing protected routes without a token returns `HTTP 401 Unauthorized`. |
| `test_protected_route_invalid_token_fails` | Accessing protected routes with tampered/forged tokens returns `HTTP 401 Unauthorized`. |
| `test_protected_route_expired_token_fails` | Accessing protected routes with tokens past their `exp` timestamp returns `HTTP 401: Token has expired`. |

---

### 6. [`tests/test_tasks.py`](test_tasks.py) — Task CRUD & IDOR Authorization
Tests complete resource lifecycle and ownership boundaries:

| Test Function | What It Validates |
| :--- | :--- |
| `test_create_task_authenticated` | Creates task via `POST /tasks/`. Verifies task is bound to the authenticated `user_id`. |
| `test_create_task_unauthenticated_fails` | Unauthenticated task creation returns `HTTP 401 Unauthorized`. |
| `test_get_single_task` | Owner can retrieve their own task by ID (`GET /tasks/{id}`). |
| `test_list_tasks_isolation` | Verifies multi-tenant isolation: User A only sees User A's tasks; User B only sees User B's tasks. |
| `test_update_task` | Owner can partially update fields via `PATCH /tasks/{id}`. |
| `test_delete_task` | Owner can delete task via `DELETE /tasks/{id}`, returning `HTTP 204 No Content`. |
| `test_ownership_enforcement_cannot_view_others_task` | **IDOR Defense:** User B requesting User A's task returns `HTTP 404 Not Found` (preventing ID enumeration). |
| `test_ownership_enforcement_cannot_update_others_task` | User B attempting to `PATCH` User A's task returns `HTTP 404`, leaving User A's task unmodified. |
| `test_ownership_enforcement_cannot_delete_others_task` | User B attempting to `DELETE` User A's task returns `HTTP 404`, leaving User A's task intact in the database. |

---

### 7. [`tests/test_queries.py`](test_queries.py) — Filtering, Sorting & Pagination
Tests query parameters, SQL expression generation, and edge cases:

| Test Function | What It Validates |
| :--- | :--- |
| `test_filter_by_status` | Tests filtering with `?status=pending`. |
| `test_filter_by_priority` | Tests filtering with `?priority=high`. |
| `test_combined_filters` | Tests composite filters with `?status=completed&priority=high`. |
| `test_sorting_by_due_date_predictable_nulls` | Tests ascending sort on deadline with `.nulls_last()`: tasks with defined deadlines appear first; tasks with `null` deadlines appear strictly at the end. |
| `test_pagination_limit_and_offset` | Tests page slicing: verifies `limit`, `offset`, `total`, and ensures Page 1 and Page 2 have disjoint ID sets. |
| `test_invalid_query_parameters_validation` | Tests Pydantic query validation: invalid status, invalid priority, invalid sort field, invalid sort order, `limit > 100`, and `offset < 0` all return `HTTP 422`. |

---

## 4. Running the Tests

### Run All Tests
```bash
pytest -v
```

### Run a Specific Test Module
```bash
pytest tests/test_auth.py -v
pytest tests/test_tasks.py -v
pytest tests/test_queries.py -v
```

### Run a Specific Test Function
```bash
pytest tests/test_tasks.py::test_ownership_enforcement_cannot_view_others_task -v
```

### Run with Print / Log Output
```bash
pytest -s -v
```

### Run with Code Coverage (optional)
```bash
pytest --cov=app --cov-report=term-missing
```
