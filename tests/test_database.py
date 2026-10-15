from unittest.mock import patch

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import engine, get_db


def test_database_engine_connection() -> None:
    """Verify that SQLAlchemy engine connects to PostgreSQL and runs queries."""
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1")).scalar()
        assert result == 1


def test_session_lifecycle() -> None:
    """Verify that get_db dependency yields a valid session and closes it cleanly."""
    db_gen = get_db()
    db = next(db_gen)

    # 1. Assert session is an instance of SQLAlchemy Session
    assert isinstance(db, Session)

    # Wrap db.close to verify it is called when request finishes
    with patch.object(db, "close", wraps=db.close) as mock_close:
        # 2. Execute a lightweight query
        result = db.execute(text("SELECT 42")).scalar()
        assert result == 42
        assert db.in_transaction()

        # 3. Simulate end of request lifecycle (generator cleanup)
        try:
            next(db_gen)
        except StopIteration:
            pass  # Expected when generator terminates

        # 4. Verify session close was called and transaction ended
        mock_close.assert_called_once()
        assert not db.in_transaction()
