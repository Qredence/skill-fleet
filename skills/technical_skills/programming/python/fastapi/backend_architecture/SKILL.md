---
name: fastapi-clean-architecture-python-3-13
description: A workflow for building scalable, maintainable FastAPI applications using
  Clean Architecture principles and Python 3.13. Covers modular directory structures,
  the repository pattern with SQLAlchemy 2.0, and async testing strategies.
category: technical_skills/programming/python/fastapi
metadata:
  skill_id: technical_skills/programming/python/fastapi/backend_architecture
  version: 1.0.0
  type: technical
---

# Clean Architecture in FastAPI with Python 3.13

Clean Architecture (or Hexagonal Architecture) ensures that your business logic is isolated from external changes. In a FastAPI context, this means your "Use Cases" don't care if you are using FastAPI, LiteStar, or a CLI; they also don't care if your database is PostgreSQL or a JSON file.

## 1. The Onion Model
Clean Architecture is often represented as a series of concentric circles:
- **Domain (Core)**: Entities and business rules. No dependencies.
- **Application (Use Cases)**: Orchestrates the flow of data. Depends only on the Domain.
- **Infrastructure (Adapters)**: Implements interfaces defined in Application (e.g., DB, Mailers).
- **Web (Entrypoints)**: FastAPI routes and controllers.

## 2. Project Structure
A standard modular structure for a `User` management component:

```text
src/
├── domain/
│   ├── entities.py        # Pure Pydantic models
│   └── exceptions.py      # Domain-specific errors
├── application/
│   ├── interfaces.py      # Abstract Repository definitions
│   └── use_cases/         # Interactors (RegisterUser, GetUser)
├── infrastructure/
│   ├── database.py        # SQLAlchemy setup
│   ├── models.py          # SQLAlchemy ORM definitions
│   └── repositories.py    # Concrete implementations
└── web/
    ├── routes.py          # FastAPI Endpoints
    ├── schemas.py         # Request/Response models
    └── dependencies.py    # DI Wiring
```

## 3. The Domain Layer (Entities)
Domain entities define the state and behavior of your business objects. They must have **zero** external dependencies on ORMs or web frameworks.

```python
# src/domain/entities.py
from dataclasses import dataclass, field
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, EmailStr

# Using Python 3.13 Type Alias syntax
type UserID = UUID

class User(BaseModel):
    model_config = ConfigDict(frozen=True) # Domain entities should be immutable
    
    id: UserID = field(default_factory=uuid4)
    email: EmailStr
    hashed_password: str
    is_active: bool = True
```

## 4. The Application Layer (Use Cases)
This layer defines **what** the system does. It defines interfaces (Protocols or ABCs) for infrastructure to implement.

```python
# src/application/interfaces.py
from typing import Protocol
from src.domain.entities import User, UserID

class IUserRepository(Protocol):
    async def get_by_email(self, email: str) -> User | None:
        ...
    async def save(self, user: User) -> User:
        ...

# src/application/use_cases/register_user.py
from src.application.interfaces import IUserRepository
from src.domain.entities import User

class RegisterUserUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def execute(self, email: str, hashed_pw: str) -> User:
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise ValueError("User already exists")
        
        user = User(email=email, hashed_password=hashed_pw)
        return await self.user_repo.save(user)
```

## 5. The Infrastructure Layer (SQLAlchemy 2.0 Async)
This layer handles the persistence logic. We map the DB Model back to the Domain Entity.

```python
# src/infrastructure/models.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Boolean
from uuid import UUID

class Base(DeclarativeBase):
    pass

class UserModel(Base):
    __tablename__ = "users"
    
    id: Mapped[UUID] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

# src/infrastructure/repositories.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.domain.entities import User
from src.infrastructure.models import UserModel

class SQLAlchemyUserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.session.execute(stmt)
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            return None
        
        return User(
            id=db_user.id,
            email=db_user.email,
            hashed_password=db_user.hashed_password,
            is_active=db_user.is_active
        )
```

## 6. The Web Layer (FastAPI Wiring)
FastAPI's Dependency Injection system acts as the "Composer" that wires the concrete Repository into the Use Case.

```python
# src/web/dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.database import get_db_session # Standard yield session
from src.infrastructure.repositories import SQLAlchemyUserRepository
from src.application.use_cases.register_user import RegisterUserUseCase

def get_user_repo(session: AsyncSession = Depends(get_db_session)):
    return SQLAlchemyUserRepository(session)

def get_register_use_case(repo: SQLAlchemyUserRepository = Depends(get_user_repo)):
    return RegisterUserUseCase(repo)

# src/web/routes.py
from fastapi import APIRouter, Depends
from src.web.schemas import UserCreate, UserResponse
from src.application.use_cases.register_user import RegisterUserUseCase

router = APIRouter()

@router.post("/users", response_model=UserResponse)
async def register(
    data: UserCreate,
    use_case: RegisterUserUseCase = Depends(get_register_use_case)
):
    user = await use_case.execute(data.email, data.password)
    return user
```

## 7. Asynchronous Testing
Because the business logic is decoupled, unit testing the Use Case is trivial and requires no database.

```python
# tests/unit/test_register_user.py
import pytest
from unittest.mock import AsyncMock
from src.application.use_cases.register_user import RegisterUserUseCase

@pytest.mark.asyncio
async def test_register_user_success():
    # Arrange
    mock_repo = AsyncMock()
    mock_repo.get_by_email.return_value = None
    use_case = RegisterUserUseCase(mock_repo)
    
    # Act
    result = await use_case.execute("test@example.com", "hash123")
    
    # Assert
    assert result.email == "test@example.com"
    mock_repo.save.assert_called_once()
```

### Key Python 3.13 Benefits
- **Type statement**: Using `type UserID = UUID` creates a readable, explorable type alias.
- **Performance**: The updated JIT (Just-In-Time) compiler and improved `asyncio` loop performance make Clean Architecture's abstraction overhead negligible.