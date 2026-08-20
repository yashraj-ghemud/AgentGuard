"""
Database base configuration and session management.

This module provides:
- SQLAlchemy engine and session factory
- Base model class for all database models
- Database session dependency for FastAPI
"""
from contextlib import contextmanager
from typing import Generator
from datetime import datetime

from sqlalchemy import create_engine, Column, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

from core.config.settings import get_settings


# Create base class for declarative models
Base = declarative_base()


class BaseModel(Base):
    """
    Base model with common fields for all database models.
    
    All models should inherit from this class to get:
    - created_at timestamp
    - updated_at timestamp (auto-updated)
    """
    __abstract__ = True

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


# Database engine
_engine = None
_SessionLocal = None


def get_engine():
    """Get or create database engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.database_url,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            echo=settings.database_echo,
            # Use pool_pre_ping to verify connections are alive
            pool_pre_ping=True,
        )
    return _engine


def get_session_factory():
    """Get or create session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
        )
    return _SessionLocal


def get_test_engine():
    """Create a test database engine with separate connection pool."""
    settings = get_settings()
    if not settings.test_database_url:
        raise ValueError("TEST_DATABASE_URL not configured")
    
    return create_engine(
        settings.test_database_url,
        poolclass=NullPool,  # No connection pooling for tests
        echo=settings.database_echo,
    )


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    
    Usage:
        with get_db_context() as db:
            # Use db session
            pass
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI routes to get database session.
    
    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            # Use db session
            pass
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database by creating all tables.
    
    This should only be used in development.
    Use Alembic migrations for production.
    """
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """
    Drop all database tables.
    
    WARNING: This is destructive! Only use in development/testing.
    """
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)


def reset_db() -> None:
    """
    Reset database by dropping and recreating all tables.
    
    WARNING: This is destructive! Only use in development/testing.
    """
    drop_db()
    init_db()
