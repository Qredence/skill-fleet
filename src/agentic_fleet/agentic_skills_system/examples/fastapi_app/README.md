# FastAPI with Async SQLAlchemy Example

Complete FastAPI application with PostgreSQL and async SQLAlchemy.

## Setup

1. **Install dependencies:**
```bash
uv sync
```

2. **Configure database:**
```bash
cp .env.example .env
# Edit .env with your PostgreSQL credentials
```

3. **Create PostgreSQL database:**
```sql
CREATE DATABASE your_db_name;
```

4. **Update DATABASE_URL in .env:**
```
DATABASE_URL=postgresql+asyncpg://your_user:your_password@localhost:5432/your_db_name
```

## Running the Application

Start the server:
```bash
uv run uvicorn src.agentic_fleet.agentic_skills_system.examples.fastapi_app.main:app --reload
```

Or run directly:
```bash
uv run python -m src.agentic_fleet.agentic_skills_system.examples.fastapi_app.main
```

## API Endpoints

- `GET /` - Root endpoint
- `GET /users` - Get all users
- `GET /users/{user_id}` - Get specific user
- `POST /users` - Create new user

## Example Usage

### Get all users
```bash
curl http://localhost:8000/users
```

### Create a user
```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "name": "John Doe"}'
```

### Get specific user
```bash
curl http://localhost:8000/users/1
```

## Project Structure

```
fastapi_app/
├── main.py          # FastAPI application and endpoints
├── database.py      # Database configuration and session management
├── models.py        # SQLAlchemy models and Pydantic schemas
├── .env.example     # Environment variables template
└── README.md        # This file
```

## Features

- Async SQLAlchemy with PostgreSQL
- Automatic table creation on startup
- Pydantic schemas for request/response validation
- Proper session management with dependency injection
- Automatic commit/rollback handling
- CORS support (can be added via FastAPI CORS middleware)
