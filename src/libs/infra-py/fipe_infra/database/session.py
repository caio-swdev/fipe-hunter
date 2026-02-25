"""
Database Session Management

Provides SQLAlchemy session factory and FastAPI dependency.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator


# Database URL from environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL", "sqlite:///./fipe_hunter.db"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database session.

    Yields:
        SQLAlchemy Session instance

    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db_session)):
            ...
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
