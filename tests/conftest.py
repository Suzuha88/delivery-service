import json
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import testing.postgresql
from httpx2 import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


@pytest.fixture(scope="session")
def postgres() -> Generator[testing.postgresql.Postgresql, None, None]:
    instance = testing.postgresql.Postgresql()
    yield instance
    instance.stop()


@pytest.fixture(scope="session")
def database_url(postgres: testing.postgresql.Postgresql) -> str:
    dsn = postgres.dsn()
    return (
        f"postgresql+asyncpg://{dsn['user']}@{dsn['host']}:{dsn['port']}/{dsn['database']}"
    )


@pytest.fixture
async def engine(database_url: str) -> AsyncGenerator[AsyncEngine, None]:
    from shared.db.models import Base

    eng = create_async_engine(database_url, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield eng

    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest.fixture
async def session_maker(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture
async def db_session(
    session_maker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    from shared.db.models import Category

    async with session_maker() as session:
        await Category.ensure_populated(session)
        yield session
        await session.rollback()


@pytest.fixture
def mock_rabbit_channel() -> MagicMock:
    channel = MagicMock()
    channel.default_exchange.publish = AsyncMock()
    return channel


@pytest.fixture
def mock_rabbit_queue() -> MagicMock:
    queue = MagicMock()
    queue.name = "hello"
    return queue


@pytest.fixture
async def api_app(
    db_session: AsyncSession,
    session_maker: async_sessionmaker[AsyncSession],
    mock_rabbit_channel: MagicMock,
    mock_rabbit_queue: MagicMock,
) -> Any:
    import main
    from shared.db import get_session

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_maker() as session:
            yield session

    main.app.dependency_overrides[get_session] = override_get_session
    main.app.state.connection = AsyncMock()
    main.app.state.channel = mock_rabbit_channel
    main.app.state.queue = mock_rabbit_queue

    yield main.app

    main.app.dependency_overrides.clear()


@pytest.fixture
async def api_client(api_app: Any) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def sample_rates_json() -> str:
    return json.dumps({"Valute": {"USD": {"Value": 90.0}}})


@pytest.fixture
def mock_incoming_message() -> MagicMock:
    message = MagicMock()

    @asynccontextmanager
    async def process():
        yield

    message.process = process
    return message
