from typing import Annotated, Any, Sequence

import uvicorn
from core.db import get_session
from fastapi import Depends, FastAPI
from models.models import Test
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)


class TestSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    text: str


@app.get("/", response_model=list[TestSchema])
async def index(
        session: Annotated[AsyncSession, Depends(get_session)]
) -> Sequence[Test]:

    res = await session.execute(select(Test))

    return res.scalars().all()
