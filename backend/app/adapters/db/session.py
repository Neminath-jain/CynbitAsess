"""Synchronous database session and engine management for SQLite."""
from collections.abc import Generator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.adapters.db.models import Base
from app.config import Settings, get_settings


class DatabaseManager:
    """Manages synchronous database engine, table creation, and session lifecycle."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        db_url = self.settings.DATABASE_URL

        # Enable check_same_thread=False for SQLite
        connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}

        self.engine: Engine = create_engine(
            db_url,
            connect_args=connect_args,
            echo=self.settings.DEBUG,
        )

        # Enforce foreign key constraints for SQLite
        if db_url.startswith("sqlite"):
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_connection: object, connection_record: object) -> None:
                cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        self.session_factory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

    def create_tables(self) -> None:
        """Create all tables defined in Base metadata."""
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self) -> None:
        """Drop all tables (used for clean test teardowns)."""
        Base.metadata.drop_all(bind=self.engine)

    def get_session(self) -> Generator[Session, None, None]:
        """Provide a transactional synchronous database session."""
        session: Session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


_db_manager_instance: DatabaseManager | None = None


def get_db_manager(settings: Settings | None = None) -> DatabaseManager:
    """Singleton getter for DatabaseManager."""
    global _db_manager_instance
    if _db_manager_instance is None or settings is not None:
        _db_manager_instance = DatabaseManager(settings)
    return _db_manager_instance
