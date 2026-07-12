from contextlib import asynccontextmanager
from typing import Annotated, Any

import uvicorn
from db.db import get_session, initialize_db
from fastapi import Depends, FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    session = await anext(get_session())
    await initialize_db(session)
    yield

app = FastAPI(lifespan=lifespan)


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
