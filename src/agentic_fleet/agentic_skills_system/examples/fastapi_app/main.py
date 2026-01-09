"""FastAPI application with async SQLAlchemy."""
from typing import List
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import engine, get_db, Base
from .models import User, UserResponse


# Create FastAPI app
app = FastAPI(
    title="FastAPI with Async SQLAlchemy",
    description="Example FastAPI app with PostgreSQL and async SQLAlchemy",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """Create database tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to FastAPI with Async SQLAlchemy"}


@app.get("/users", response_model=List[UserResponse])
async def get_users(db: AsyncSession = Depends(get_db)):
    """
    Get all users from the database.

    Returns:
        List[UserResponse]: List of all users
    """
    # Execute query to get all users
    result = await db.execute(select(User))
    users = result.scalars().all()

    return users


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a specific user by ID.

    Args:
        user_id: The user's ID
        db: Database session

    Returns:
        UserResponse: The user data

    Raises:
        HTTPException: If user not found
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@app.post("/users", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new user.

    Args:
        user: User data from request body
        db: Database session

    Returns:
        UserResponse: The created user
    """
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user
    db_user = User(email=user.email, name=user.name)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
