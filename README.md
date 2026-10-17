# Task Management REST API

A production-ready, human-quality Task Management REST API built with **Python 3.14**, **FastAPI**, **PostgreSQL**, **SQLAlchemy 2.0**, **Alembic**, **JWT Authentication (Argon2)**, and **Pytest**.

This repository is designed to reflect the standards of a thoughtful backend engineer: readable code, correct business logic, appropriate security, query-level authorization (IDOR prevention), fully isolated automated tests, and clean architecture.

---

## 1. System Architecture & Tech Stack

```
                  ┌──────────────────────────────────────────────┐
                  │                 FastAPI App                  │
                  │                                              │
Client (HTTP) ───▶│  ┌──────────────┐     ┌───────────────────┐  │
                  │  │ Pydantic v2  │────▶│ Dependency        │  │
                  │  │ Validation   │     │ Injection         │  │
                  │  └──────────────┘     │ (get_current_user)│  │
                  │                       │ (get_db)          │  │
                  │                       └─────────┬─────────┘  │
                  │                                 │            │
                  │                                 ▼            │
                  │                       ┌───────────────────┐  │
                  │                       │ SQLAlchemy 2.0    │  │
                  │                       │ (Mapped Models)   │  │
                  │                       └─────────┬─────────┘  │
                  └─────────────────────────────────┼────────────┘
                                                    │
                                                    ▼
                                    ┌───────────────────────────────┐
                                    │      PostgreSQL Database      │
                                    │  - Development: task_db       │
                                    │  - Automated Test: task_test_db│
                                    └───────────────────────────────┘
```

| Technology | Purpose & Responsibility |
| :--- | :--- |
| **Python 3.12+** | Core programming language using modern syntax, `enum.StrEnum`, and strict type annotations. |
| **FastAPI** | High-performance ASGI framework handling routing, request/response validation, dependency injection, and automatic OpenAPI documentation. |
| **PostgreSQL** | Primary relational database using foreign key constraints, composite indexes, and transactional DDL. |
| **SQLAlchemy 2.0** | Modern ORM using `Mapped` and `mapped_column`, relationship cascades, and explicit session management. |
| **Alembic** | Database migration manager version-controlling schema changes and synchronizing models with PostgreSQL. |
| **Pydantic v2** | Request validation and response serialization schemas (`from_attributes=True`), keeping API contracts separate from ORM entities. |
| **pwdlib (Argon2)** | Memory-hard, state-of-the-art password hashing resistant to GPU and ASIC brute-force attacks. |
| **PyJWT** | Cryptographic generation and validation of stateless JWT access tokens (`HS256`). |
| **Pytest & TestClient** | Automated integration and unit testing with isolated test database fixtures and `app.dependency_overrides`. |
| **Ruff** | Ultra-fast Python linter and code formatter. |

---

## 2. Key Engineering Highlights

- **Stateless JWT Authentication:** Secure login flow issuing signed JWT access tokens with expiration timestamps. Plaintext passwords and hashes are never exposed in API responses.
- **Insecure Direct Object Reference (IDOR) Defense:** Every task operation strictly enforces user ownership at the SQL query level (`Task.user_id == current_user.id`). Unauthorized access attempts return `HTTP 404 Not Found` to prevent resource enumeration.
- **Dynamic Queries & Deterministic Nulls:** Supports filtering by `status` and `priority`, sorting by `created_at` or `due_date`, and ensures predictable sorting for null deadlines via `.nulls_last()`.
- **Envelope Pagination:** Paginated endpoints return an envelope containing `items`, `total`, `limit`, and `offset` for frontend page calculations.
- **Dual-Database Test Isolation:** Dedicated `task_test_db` ensures automated test runs never delete or contaminate active development data.

---

## 3. Project Directory Structure

```text
Task Management REST API/
├── alembic/                      # Database migrations
│   ├── env.py                    # Alembic environment configured with app settings
│   └── versions/                 # Version-controlled migration scripts
├── alembic.ini                   # Alembic CLI configuration
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI application factory and OpenAPI configuration
│   ├── api/
│   │   ├── deps.py               # Dependency injection (get_current_user, get_db)
│   │   └── v1/
│   │       ├── api.py            # Central router mounting all v1 endpoints
│   │       └── endpoints/
│   │           ├── auth.py       # Register, login, and /me endpoints
│   │           ├── health.py     # Health check and DB readiness probe
│   │           └── tasks.py      # Task CRUD with filtering, sorting, pagination
│   ├── core/
│   │   ├── config.py             # Pydantic-settings configuration (.env loader)
│   │   ├── database.py           # SQLAlchemy 2.0 engine, SessionLocal, Base
│   │   └── security.py           # Argon2 password hashing & JWT token encoding
│   ├── models/                   # SQLAlchemy ORM database models
│   │   ├── __init__.py
│   │   ├── task.py               # Task model, TaskStatus, TaskPriority
│   │   └── user.py               # User model with cascade delete relationships
│   └── schemas/                  # Pydantic request & response schemas
│       ├── __init__.py
│       ├── health.py             # HealthCheckResponse schema
│       ├── task.py               # TaskCreate, TaskUpdate, TaskResponse, PaginatedTaskResponse
│       ├── token.py              # Token and TokenPayload schemas
│       └── user.py               # UserCreate and UserResponse schemas
├── tests/                        # Automated Pytest test suite
│   ├── conftest.py               # Test database setup and dependency overrides
│   ├── test_auth.py              # Authentication and JWT validation tests
│   ├── test_database.py          # Engine and session lifecycle tests
│   ├── test_health.py            # Health check tests
│   ├── test_models.py            # Model constraints and cascade delete tests
│   ├── test_queries.py           # Filtering, sorting, nulls, and pagination tests
│   └── test_tasks.py             # Task CRUD and IDOR authorization tests
├── .env                          # Local secrets (never committed to Git)
├── .env.example                  # Environment template for team onboarding
├── .gitignore                    # Git exclusion rules
├── pyproject.toml                # Ruff and Pytest configuration
└── requirements.txt              # Pinned Python package dependencies
```

---

## 4. Setup and Installation

### Prerequisites
- Python 3.12+ (Python 3.14 supported)
- PostgreSQL 15+ installed and running

### Step 1: Clone Repository and Create Virtual Environment
```bash
git clone https://github.com/prashant-prog/Task-Management-REST-API.git
cd Task-Management-REST-API

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Configure PostgreSQL Databases
Open `psql` as the PostgreSQL administrator and create the dedicated database user and databases:

```bash
# 1. Start and enable PostgreSQL (if not already running)
sudo systemctl enable --now postgresql

# 2. Create the development database and user
sudo -u postgres psql -c "CREATE USER task_user WITH PASSWORD 'task_password';"
sudo -u postgres psql -c "CREATE DATABASE task_db OWNER task_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE task_db TO task_user;"

# 3. Create the dedicated test database (for automated tests)
sudo -u postgres psql -c "CREATE DATABASE task_test_db OWNER task_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE task_test_db TO task_user;"
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Review your `.env` settings:
```dotenv
PROJECT_NAME="Task Management REST API"
ENVIRONMENT="development"
DEBUG=True

DATABASE_URL="postgresql+psycopg://task_user:task_password@localhost:5432/task_db"
TEST_DATABASE_URL="postgresql+psycopg://task_user:task_password@localhost:5432/task_test_db"

# Generate a secure key in terminal using: openssl rand -hex 32
SECRET_KEY="replace-this-with-a-secure-random-secret-key"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### Step 4: Run Database Migrations
Apply all schema migrations to create the database tables:
```bash
alembic upgrade head
```

---

## 5. Running the Application

Start the development server with Uvicorn in auto-reload mode:
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- **Interactive Swagger Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check Endpoint:** [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

---

## 6. API Reference & Example Requests

### Endpoints Overview

| Method | Path | Auth Required | Description |
| :--- | :--- | :---: | :--- |
| `GET` | `/` | No | Root welcome endpoint with API documentation links |
| `GET` | `/api/v1/health` | No | Operational readiness and database connectivity probe |
| `POST` | `/api/v1/auth/register` | No | Register a new user account (returns 201 Created) |
| `POST` | `/api/v1/auth/login` | No | Authenticate credentials and receive a signed JWT access token |
| `GET` | `/api/v1/auth/me` | **Yes** | Retrieve authenticated user profile |
| `POST` | `/api/v1/tasks/` | **Yes** | Create a new task owned by the authenticated user |
| `GET` | `/api/v1/tasks/` | **Yes** | List tasks with filtering, sorting, and pagination |
| `GET` | `/api/v1/tasks/{id}` | **Yes** | Retrieve a single task by ID (owner only) |
| `PATCH` | `/api/v1/tasks/{id}` | **Yes** | Partially update a task (owner only) |
| `DELETE` | `/api/v1/tasks/{id}` | **Yes** | Delete a task (owner only, returns 204 No Content) |

---

### Example cURL Workflows

#### 1. Register a User
```bash
curl -i -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "alex@example.com", "password": "SecurePassword123."}'
```

#### 2. Log In & Store Access Token
```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -d "username=alex@example.com&password=SecurePassword123." \
  | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
```

#### 3. View Current User Profile
```bash
curl -i -X GET http://127.0.0.1:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

#### 4. Create a Task
```bash
curl -i -X POST http://127.0.0.1:8000/api/v1/tasks/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Prepare system architecture presentation",
    "description": "Outline database models, JWT authentication, and IDOR prevention.",
    "status": "in_progress",
    "priority": "high",
    "due_date": "2026-10-30T18:00:00Z"
  }'
```

#### 5. List Tasks with Filtering, Sorting, and Pagination
```bash
# Filter by status and priority, sorted by deadline ascending (nulls last), page limit 5:
curl -i -X GET "http://127.0.0.1:8000/api/v1/tasks/?status=in_progress&priority=high&sort_by=due_date&order=asc&limit=5&offset=0" \
  -H "Authorization: Bearer $TOKEN"
```

#### 6. Partially Update a Task
```bash
curl -i -X PATCH http://127.0.0.1:8000/api/v1/tasks/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'
```

#### 7. Delete a Task
```bash
curl -i -X DELETE http://127.0.0.1:8000/api/v1/tasks/1 \
  -H "Authorization: Bearer $TOKEN"
```

---

## 7. Automated Testing & Code Quality

### Running Tests
Execute the full test suite using Pytest. Tests run in complete isolation against `task_test_db`:

```bash
pytest -v
```

All 32 tests covering database connectivity, session lifecycles, model relationships, unique email constraints, cascade deletes, registration, login, JWT validation, expiration, CRUD operations, IDOR ownership isolation, filtering, sorting, and pagination will execute and pass.

### Linting and Code Formatting
Check and format Python code using Ruff:

```bash
# Check for lint errors
ruff check .

# Format code
ruff format .
```

---

## 8. License

This project is licensed under the MIT License.
