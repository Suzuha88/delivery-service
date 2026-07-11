from contextlib import asynccontextmanager
from typing import Annotated, Any

import uvicorn
from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from core.db import get_session, initialize_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    session = await anext(get_session())
    await initialize_db(session)
    yield

app = FastAPI(lifespan=lifespan)


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)


@app.post("/register")
async def register(session: Annotated[AsyncSession, Depends(get_session)]) -> dict[str, Any]:

    return {"response": 0}


@app.get("/")
async def index(
        session: Annotated[AsyncSession, Depends(get_session)]
):
    return settings.DATABASE_URL_WITHOUT_CLIENT
