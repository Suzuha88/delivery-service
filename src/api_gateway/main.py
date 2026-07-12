from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI
from schemas.schemas import PackageSchema


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(lifespan=lifespan)


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)


@app.post("/register")
async def register(
        package: PackageSchema,
) -> dict[str, Any]:

    return {"response": 0}


@app.get("/")
async def index(
) -> None: pass
