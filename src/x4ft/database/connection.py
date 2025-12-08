"""Database connection management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

from .schema import Base


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self, database_path: Path):
        """Initialize database manager.

        Args:
            database_path: Path to SQLite database file
        """
        self.database_path = database_path
        self.engine = create_engine(
            f"sqlite:///{database_path}",
            echo=False,  # Set to True for SQL debugging
            connect_args={"check_same_thread": False}  # Allow multi-threading
        )
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False
        )

    def create_tables(self) -> None:
        """Create all tables if they don't exist."""
        Base.metadata.create_all(self.engine)

    def drop_tables(self) -> None:
        """Drop all tables (useful for re-extraction)."""
        Base.metadata.drop_all(self.engine)

    def recreate_tables(self) -> None:
        """Drop and recreate all tables."""
        self.drop_tables()
        self.create_tables()

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session with automatic cleanup.

        Yields:
            SQLAlchemy Session

        Example:
            with db_manager.get_session() as session:
                ship = session.query(Ship).first()
                print(ship.name)
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_raw_session(self) -> Session:
        """Get a raw session without context management.

        Note: You must manually close this session!

        Returns:
            SQLAlchemy Session
        """
        return self.SessionLocal()

    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database.

        Args:
            table_name: Name of the table to check

        Returns:
            True if table exists, False otherwise
        """
        from sqlalchemy import inspect
        inspector = inspect(self.engine)
        return table_name in inspector.get_table_names()

    def get_row_count(self, table_name: str) -> int:
        """Get number of rows in a table.

        Args:
            table_name: Name of the table

        Returns:
            Number of rows, or 0 if table doesn't exist
        """
        if not self.table_exists(table_name):
            return 0

        from sqlalchemy import text
        with self.get_session() as session:
            result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            return result.scalar()

    def database_exists(self) -> bool:
        """Check if database file exists.

        Returns:
            True if database file exists
        """
        return self.database_path.exists()

    def database_is_populated(self) -> bool:
        """Check if database exists and has data.

        Returns:
            True if database has ships and equipment
        """
        if not self.database_exists():
            return False

        try:
            ship_count = self.get_row_count('ships')
            equipment_count = self.get_row_count('equipment')
            return ship_count > 0 and equipment_count > 0
        except Exception:
            return False
