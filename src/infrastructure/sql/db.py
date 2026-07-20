from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.core.config import db_settings

URL = db_settings.database_url

async_engine = create_async_engine(
    URL,
    echo=False,
)

async_session_maker = async_sessionmaker(bind=async_engine, expire_on_commit=False)
