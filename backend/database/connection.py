"""SQLite engine and session factory."""

from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.config import settings


def _get_engine():
    db_url = settings.database_url
    # Ensure data directory exists for SQLite
    if db_url.startswith("sqlite:///"):
        db_path = Path(db_url.replace("sqlite:///", ""))
        db_path.parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(db_url, connect_args={"check_same_thread": False} if "sqlite" in db_url else {})

    # Enable WAL mode and foreign keys for SQLite
    if "sqlite" in db_url:

        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


engine = _get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency: yields a database session."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables() -> None:
    """Create all ORM-defined tables and apply lightweight column migrations (idempotent)."""
    from backend.database import models  # noqa: F401  # registers models

    Base.metadata.create_all(bind=engine)
    _migrate_add_columns()


def _migrate_add_columns() -> None:
    """Add new columns to existing tables via raw SQL if they don't already exist.

    SQLAlchemy's create_all does not ALTER existing tables, so new nullable columns
    must be added manually. Safe to call repeatedly — no-ops if columns already exist.
    """
    _new_columns = [
        ("sources", "economic_school", "TEXT"),
        ("sources", "economic_bias", "TEXT"),
        ("sources", "salience_domains", "TEXT"),
        ("sources", "analytical_framework", "TEXT"),
    ]
    with engine.connect() as conn:
        for table, column, col_type in _new_columns:
            existing = [
                row[1] for row in conn.execute(__import__("sqlalchemy").text(f"PRAGMA table_info({table})")).fetchall()
            ]
            if column not in existing:
                conn.execute(__import__("sqlalchemy").text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                conn.commit()
