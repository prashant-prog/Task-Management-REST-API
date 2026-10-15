from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# 1. Create SQLAlchemy Engine
# pool_pre_ping=True checks connections before using them
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
)

# 2. Create SessionLocal factory
# autocommit=False ensures transactions are explicitly controlled
# autoflush=False prevents premature flushes before commit
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# 3. SQLAlchemy 2.0 Declarative Base
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy 2.0 ORM models."""


# 4. Dependency Injection function for FastAPI
def get_db() -> Generator[Session, None, None]:
    """Provide a transactional database session per request.

    Yields a SQLAlchemy Session and guarantees it is closed when
    the HTTP request processing completes, returning the connection
    to the pool.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
