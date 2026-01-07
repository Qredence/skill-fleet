from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db

app = FastAPI()


@app.get("/users/me")
async def read_users_me(db: AsyncSession = Depends(get_db)):
    # Use db to query user
    return {"user_id": "123"}
