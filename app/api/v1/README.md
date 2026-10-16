# API Version 1 (`app/api/v1/`)

This package groups all version 1 endpoints for the **Task Management REST API**. It acts as the assembly hub that unites individual endpoint modules under a unified, versioned routing prefix.

---

## 1. Directory Structure

```text
app/api/v1/
├── __init__.py           # Package marker for v1 API
├── api.py                # Central APIRouter mounting all v1 endpoint routers
├── endpoints/            # Dedicated endpoint handler modules
│   ├── auth.py           # User registration, login, and profile
│   ├── health.py         # Readiness probe and database health
│   ├── tasks.py          # Task CRUD with filtering, sorting, pagination
│   └── README.md         # Documentation for route handlers
└── README.md             # This documentation file
```

---

## 2. Central Router (`app/api/v1/api.py`)

The [`api.py`](api.py) module instantiates the top-level `api_router` and mounts sub-routers with their respective tags and prefixes:

```python
from fastapi import APIRouter
from app.api.v1.endpoints import auth, health, tasks

api_router = APIRouter()

# Health probe (unauthenticated)
api_router.include_router(health.router, tags=["Health"])

# Authentication endpoints: /api/v1/auth/*
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Task management endpoints: /api/v1/tasks/*
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
```

In [`app/main.py`](../../main.py), this router is mounted to the application instance:
```python
app.include_router(api_router, prefix=settings.API_V1_STR)  # /api/v1
```

---

## 3. OpenAPI Documentation Tags

The `tags` declared here are consumed by FastAPI to group endpoints visually in the interactive Swagger UI (`/docs`) and ReDoc (`/redoc`):

- **`Health`:** Public endpoints to check system readiness.
- **`Authentication`:** Public endpoints to register and authenticate, plus protected `/auth/me`.
- **`Tasks`:** Protected endpoints requiring a Bearer token to perform task operations.
