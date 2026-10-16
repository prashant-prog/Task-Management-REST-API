# Core Module (`app/core/`)

This directory houses cross-cutting infrastructure services: configuration management, database connectivity, and cryptographic security. These utilities are foundational to the application and are consumed across models, endpoints, and migrations.

---

## 1. Directory Structure

```text
app/core/
├── __init__.py           # Package marker for core module
├── config.py             # Strongly typed settings loaded via pydantic-settings
├── database.py           # SQLAlchemy 2.0 Engine, SessionLocal, Base, get_db
├── security.py           # Argon2 password hashing and JWT encoding/decoding
└── README.md             # This documentation file
```

---

## 2. Modules Breakdown

### 1. [`config.py`](config.py) — 12-Factor Settings Management
Loads and validates environment variables from `.env` and OS environment into a typed singleton `settings`:

- **Attributes:**
  - `PROJECT_NAME`: Title of the API.
  - `ENVIRONMENT`: Runtime environment (`development`, `production`, `test`).
  - `DEBUG`: Boolean flag controlling verbose error outputs.
  - `API_V1_STR`: API route prefix (`/api/v1`).
  - `DATABASE_URL`: PostgreSQL connection string for development (`task_db`).
  - `TEST_DATABASE_URL`: PostgreSQL connection string for automated testing (`task_test_db`).
  - `SECRET_KEY`: Cryptographic signing secret for JWT tokens.
  - `ALGORITHM`: Token signing algorithm (`HS256`).
  - `ACCESS_TOKEN_EXPIRE_MINUTES`: Expiration window for access tokens (60 minutes).
- **Behavior:** Fails fast at startup if required configuration parameters are missing or malformed.

---

### 2. [`database.py`](database.py) — SQLAlchemy 2.0 Persistence Engine
Configures database connectivity and session lifecycle:

- **`engine`:**
  - Initialized with `pool_pre_ping=True`: sends a lightweight ping to PostgreSQL before checking out a connection from the pool. If an idle TCP connection was terminated by firewall or server restart, it reconnects automatically.
- **`SessionLocal`:**
  - A thread-local session factory with `autocommit=False` and `autoflush=False`, giving route handlers explicit transaction control.
- **`Base`:**
  - Subclasses SQLAlchemy 2.0 `DeclarativeBase`. All ORM models inherit from this class.
- **`get_db()`:**
  - Generator function used as a FastAPI dependency (`Depends(get_db)`).
  - Uses `try ... finally: db.close()` to guarantee that every checked-out connection is returned to the connection pool, preventing connection leaks.

---

### 3. [`security.py`](security.py) — Cryptography & Authentication
Handles password hashing and stateless token operations:

- **Password Hashing (Argon2):**
  - Uses `pwdlib` backed by `Argon2Hasher`.
  - Argon2 is memory-hard and GPU-resistant, protecting passwords against hardware-accelerated cracking.
  - `get_password_hash(password: str) -> str`: Produces salted, cryptographic hashes.
  - `verify_password(plain_password: str, hashed_password: str) -> bool`: Constant-time comparison preventing timing attacks.
- **JWT Token Management:**
  - `create_access_token(subject, expires_delta) -> str`: Encodes claims (`sub: user_id`, `exp`, `iat`) into signed JSON Web Tokens using `HS256`.
