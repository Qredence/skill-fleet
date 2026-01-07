### Composition Patterns

- **Database Integration**: Connect `async_db_conn.py` with SQLAlchemy or Tortoise-ORM. Use the Dependency Injection pattern to yield a session/connection, ensuring it is closed after the request.
- **Authentication**: Integrate `auth_flow.py` with external Identity Providers or local JWT logic. Use `Security` dependencies to enforce scopes.
- **DevOps/Deployment**:
    - Use `uvicorn` or `hypercorn` as the ASGI server.
    - Dockerize by using a multi-stage build starting from `python:3.11-slim`.
    - Set `root_path` when deploying behind a reverse proxy (Nginx/Traefik).
- **Testing**: Use `httpx.AsyncClient` alongside `pytest-asyncio` to test endpoints without running a real server.