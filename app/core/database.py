"""
Database connection setup and session management for SQLAlchemy.
Provides async engine and session factory for the application.
"""

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Create async engine
# SQLite doesn't support pool_size/max_overflow parameters
try:
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        future=True,
    )

    # Create async session factory
    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    database_available = True
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    engine = None
    AsyncSessionLocal = None
    database_available = False

# Base class for all models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    Dependency to get database session.
    Usage: async def endpoint(db: AsyncSession = Depends(get_db)):
    """
    if not database_available or not AsyncSessionLocal:
        raise RuntimeError("Database is not available. Please check configuration and dependencies.")
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    if not database_available or not engine:
        raise RuntimeError("Cannot initialize database - engine not available")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections."""
    if engine:
        await engine.dispose()
