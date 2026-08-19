"""
Core database configuration and session management.

Uses SQLAlchemy with SQLite and Alembic for migrations.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger("core.database")


# Base class for all models
class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


# Create async engine with SQLite-specific configuration
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.app_debug,  # SQL logging in debug mode
    poolclass=StaticPool,  # SQLite works best with single connection
    connect_args={"check_same_thread": False},
)

# Async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db() -> None:
    """Initialize database tables."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
    logger.info("Database connections closed")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.

    Yields:
        AsyncSession: Database session

    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_session() -> AsyncSession:
    """
    Get a database session for use outside of request context.

    Note: Caller is responsible for closing the session.

    Returns:
        AsyncSession: Database session

    Usage:
        async with get_db_session() as session:
            # do something
    """
    return async_session_maker()


# Convenience function for running queries outside request context
async def db_query(func):
    """Decorator for database operations outside request context."""
    async def wrapper(*args, **kwargs):
        async with async_session_maker() as session:
            try:
                result = await func(session, *args, **kwargs)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
    return wrapper
