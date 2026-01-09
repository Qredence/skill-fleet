"""Database configuration for async SQLAlchemy."""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import AsyncEngine

# Database URL - adjust for your PostgreSQL setup
DATABASE_URL = "postgresql+asyncpg://user:password@localhost/dbname"

# Create async engine
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True
)

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base class for models
Base = declarative_base()


# Dependency to get database session
async def get_db():
    """Dependency function to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
