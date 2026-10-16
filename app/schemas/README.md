# Pydantic Schemas (`app/schemas/`)

This directory contains the **Pydantic v2 schemas** that define the data validation, serialization, and API contract layer of the application.

---

## 1. Directory Structure

```text
app/schemas/
├── __init__.py           # Re-exports all schemas for clean, centralized imports
├── health.py             # Health check response schemas
├── token.py              # JWT authentication tokens and payload schemas
├── user.py               # User creation, update, and response schemas
├── task.py               # Task schemas, pagination envelopes, and sorting enums
└── README.md             # This documentation file
```

---

## 2. Architectural Principles

### 1. Separation of Persistence and Presentation
- **SQLAlchemy Models (`app/models/`)** govern database tables, foreign keys, and SQL operations.
- **Pydantic Schemas (`app/schemas/`)** govern the public HTTP API contract, enforcing strict validation on incoming JSON payloads and stripping sensitive internal fields on outgoing responses.

### 2. Security & Zero-Trust Input Design
- **Password Exposure Prevention**: `UserCreate` accepts the plaintext `password` during registration, but `UserResponse` never includes `hashed_password`, ensuring database hashes are never exposed via the API.
- **IDOR Protection by Design**: `TaskCreate` does not accept a `user_id` in the request body. The owning `user_id` is derived server-side from the verified JWT access token, preventing users from forging task assignments.
- **Granular Updates**: `TaskUpdate` marks all fields as optional (`None`), allowing clients to perform partial updates (`PATCH`) without overwriting unspecified attributes.

### 3. Pydantic v2 ORM Integration (`from_attributes=True`)
Response schemas define `model_config = ConfigDict(from_attributes=True)`. This replaces Pydantic v1's `orm_mode = True` and allows FastAPI to automatically convert SQLAlchemy 2.0 ORM instances into serialized JSON responses:

```python
# Automatic conversion from ORM model to serialized schema
task_response = TaskResponse.model_validate(db_task)
```

---

## 3. Schemas Breakdown

### [`health.py`](health.py) — Health Monitoring
- `HealthCheckResponse`:
  - `status`: `"ok"` or error indicator.
  - `app_name`: Configured application title.
  - `environment`: Active runtime environment (`development`, `production`).
  - `database`: PostgreSQL connection status (`"connected"` or error message).

---

### [`token.py`](token.py) — Authentication & Claims
- `Token`:
  - `access_token`: The signed JSON Web Token string.
  - `token_type`: Default `"bearer"`.
- `TokenPayload`:
  - `sub`: Subject identifier stored in token claims (contains user email as string).

---

### [`user.py`](user.py) — User Accounts
- `UserBase`: Shared fields between user requests and responses.
  - `email`: Validated via Pydantic's `EmailStr` (requires `email-validator`).
- `UserCreate` (Inherits `UserBase`):
  - `password`: String with strict validation: minimum 8 characters, maximum 128 characters.
- `UserResponse` (Inherits `UserBase`):
  - `id`: Unique user identifier (Integer).
  - `is_active`: Account status (Boolean).
  - `created_at` & `updated_at`: UTC timestamps (`datetime`).
  - Configured with `from_attributes=True`.

---

### [`task.py`](task.py) — Task Management & Pagination

#### Sorting & Query Enums
- `TaskSortField` (`enum.StrEnum`): Permitted fields for ordering (`created_at`, `due_date`).
- `SortOrder` (`enum.StrEnum`): Permitted sort directions (`asc`, `desc`).

#### Data Models
- `TaskBase`: Common task attributes.
  - `title`: String (`min_length=1`, `max_length=255`).
  - `description`: Optional text string (`str | None`).
  - `status`: Validated against `TaskStatus` enum (`pending`, `in_progress`, `completed`). Defaults to `pending`.
  - `priority`: Validated against `TaskPriority` enum (`low`, `medium`, `high`). Defaults to `medium`.
  - `due_date`: Optional timezone-aware timestamp (`datetime | None`).
- `TaskCreate` (Inherits `TaskBase`):
  - Request body for creating tasks. Does not expose `user_id`.
- `TaskUpdate` (`BaseModel`):
  - Request body for modifying tasks via `PATCH`. Every field is optional (`None` default) so clients only transmit modified fields.
- `TaskResponse` (Inherits `TaskBase`):
  - Output response body for a single task.
  - Includes `id`, `user_id`, `created_at`, `updated_at`.
  - Configured with `from_attributes=True`.
- `PaginatedTaskResponse`:
  - Envelope response for paginated list endpoints:
    - `items`: List of `TaskResponse` objects.
    - `total`: Total matching records count (`ge=0`).
    - `limit`: Page limit used (`ge=1`).
    - `offset`: Record offset applied (`ge=0`).

---

## 4. Request vs. Response Matrix

| Entity | Action | Schema Used | Sensitive Fields Filtered |
| :--- | :--- | :--- | :--- |
| **Auth** | Login Request | Form (`username`, `password`) | Password validated & discarded |
| **Auth** | Login Response | `Token` | No credentials returned, only bearer token |
| **User** | Register Request | `UserCreate` | Plaintext password received for hashing |
| **User** | Register/Read | `UserResponse` | Password hash strictly excluded |
| **Task** | Create Request | `TaskCreate` | `user_id` excluded (inferred from JWT) |
| **Task** | Update Request | `TaskUpdate` | Partial updates only; all fields optional |
| **Task** | Single View | `TaskResponse` | Fully serialized with owner ID & timestamps |
| **Task** | Paginated List | `PaginatedTaskResponse` | Encapsulates items with pagination metadata |
