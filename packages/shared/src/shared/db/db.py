from pathlib import Path
from typing import AsyncGenerator

from alembic.config import Config, command
from alembic.script import ScriptDirectory
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..config import settings
from .models import Category

URL = settings.DATABASE_URL

async_engine = create_async_engine(
    URL,
    echo=False,
)

AsyncSessionMaker = async_sessionmaker(
    bind=async_engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionMaker() as session:
        yield session


async def initialize_db() -> None:
    alembic_cfg_path = Path(__file__).parent.parent / "alembic.ini"
    alembic_cfg = Config(str(alembic_cfg_path))

    script = ScriptDirectory.from_config(alembic_cfg)
    current_rev = script.get_current_head()

    if not current_rev:
        command.revision(
            alembic_cfg,
            autogenerate=True,
            message="Initializing db",
            head="head"
        )
    command.upgrade(alembic_cfg, "head")

    async with AsyncSessionMaker() as session:
        await Category.ensure_populated(session)
