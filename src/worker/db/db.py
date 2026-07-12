from typing import Annotated, AsyncGenerator

from fastapi import Depends
from models.models import Category
from shared.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

URL = settings.DATABASE_URL

async_engine = create_async_engine(
    URL,
    echo=True)

AsyncSessionMaker = async_sessionmaker(
    bind=async_engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionMaker() as session:
        yield session


async def initialize_db() -> None:
    async with AsyncSessionMaker() as session:
        await Category.ensure_populated(session)
