# Application Package (`app/`)

This directory contains the entire application source code for the **Task Management REST API**, structured as a modular Python package.

---

## 1. Package Architecture

```text
app/
├── __init__.py           # Package marker for the application
├── main.py               # FastAPI application factory and OpenAPI documentation entry point
├── api/                  # HTTP layer: routers, route handlers, and dependency injection
├── core/                 # Cross-cutting concerns: config, security (Argon2/JWT), database engine
├── models/               # SQLAlchemy 2.0 ORM database entities
└── schemas/              # Pydantic v2 data validation and response serialization schemas
```

---

## 2. Layer Responsibilities & Separation of Concerns

```
HTTP Request ──▶ [ app/main.py ]
                       │
                       ▼
                 [ app/api/ ] ── (Uses app/api/deps.py for Auth & DB Session)
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
  [ app/schemas/ ]            [ app/models/ ]
  (Request Validation)        (SQLAlchemy ORM Entities)
         │                           │
         │                           ▼
         └──────────────────▶ [ app/core/database.py ]
                                     │
                                     ▼
                            PostgreSQL Database
```

| Subpackage / File | Primary Responsibility |
| :--- | :--- |
| **[`main.py`](main.py)** | Instantiates the `FastAPI` application, configures OpenAPI documentation (`/docs`, `/redoc`), and mounts the versioned API routers. |
| **[`api/`](api/)** | Translates incoming HTTP requests, handles status codes, and coordinates dependencies. |
| **[`core/`](core/)** | Infrastructure-level modules: configuration loading (`config.py`), database connection pooling (`database.py`), and cryptographic password/token hashing (`security.py`). |
| **[`models/`](models/)** | Declares persistent database entities using SQLAlchemy 2.0 `Mapped` columns, constraints, and relationships. |
| **[`schemas/`](schemas/)** | Defines strict data contracts using Pydantic v2. Ensures client inputs are validated and sensitive database fields (e.g., passwords) are never returned. |

---

## 3. The FastAPI Request Lifecycle

When a request arrives at the application:

1. **Uvicorn ASGI Server:** Receives raw HTTP bytes and passes the ASGI request scope to `app.main:app`.
2. **Router Matching:** FastAPI traverses the route table in `app/api/v1/api.py` to locate the matching endpoint.
3. **Dependency Injection:** Injected dependencies in `app/api/deps.py` run before the route handler:
   - `get_db`: Checks out an active connection from the SQLAlchemy pool and yields a session.
   - `get_current_user`: Extracts the Bearer token, validates the JWT signature, and queries the user.
4. **Input Validation:** Request body is parsed and validated against the Pydantic schema (e.g. `TaskCreate`).
5. **Route Handler:** Executes business logic and database queries using SQLAlchemy 2.0 syntax.
6. **Response Serialization:** Output is serialized through `response_model` (e.g. `TaskResponse`), filtering out internal attributes.
7. **Cleanup:** Execution returns to `get_db`'s `finally:` block, calling `db.close()` to release the connection back to the pool.
