# API Layer (`app/api/`)

This directory represents the **HTTP boundary** of the application. It is responsible for routing HTTP requests, coordinating dependency injection, and enforcing authentication/authorization rules before dispatching work to the database and schema layers.

---

## 1. Directory Structure

```text
app/api/
├── __init__.py           # Package marker for API layer
├── deps.py               # Centralized FastAPI dependency injection providers
├── v1/                   # Version 1 API router and endpoint implementations
│   ├── api.py            # Aggregator mounting all v1 endpoint routers
│   └── endpoints/        # Individual route handler modules (health, auth, tasks)
└── README.md             # This documentation file
```

---

## 2. Dependency Injection (`app/api/deps.py`)

FastAPI's dependency injection system allows route handlers to declare their requirements (database sessions, authenticated users) as function parameters. This eliminates global variables and makes route handlers easy to test.

### Key Dependencies in [`deps.py`](deps.py)

1. **`oauth2_scheme = OAuth2PasswordBearer(tokenUrl=...)`:**
   - Registers the OAuth2 password grant flow with FastAPI.
   - Extracts the token from the HTTP request header: `Authorization: Bearer <token>`.
   - Powers the interactive **"Authorize"** button in Swagger UI (`/docs`).

2. **`get_current_user`:**
   ```python
   def get_current_user(
       db: Annotated[Session, Depends(get_db)],
       token: Annotated[str, Depends(oauth2_scheme)],
   ) -> User:
   ```
   - Decodes the JWT token using `settings.SECRET_KEY` and `settings.ALGORITHM`.
   - Checks expiration (`exp`) and subject (`sub = user.id`).
   - Handles `jwt.ExpiredSignatureError` by raising `HTTP 401 Unauthorized: Token has expired`.
   - Fetches the user from PostgreSQL using `db.get(User, user_id)`.
   - Raises `HTTP 401 Unauthorized` if the token is invalid or the user no longer exists.

3. **`get_current_active_user`:**
   ```python
   def get_current_active_user(
       current_user: Annotated[User, Depends(get_current_user)],
   ) -> User:
   ```
   - Chains directly on top of `get_current_user`.
   - Validates that `current_user.is_active is True`.
   - Protects against suspended or deactivated accounts accessing the API.

---

## 3. API Versioning Strategy

All active endpoints are grouped under [`v1/`](v1/).

- The central router in `v1/api.py` mounts sub-routers with logical prefixes (`/auth`, `/tasks`).
- Prefixing routes with `/api/v1` protects external clients from breaking changes if a future `/api/v2` is introduced.
