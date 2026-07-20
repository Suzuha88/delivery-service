import json
import os
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import testing.postgresql
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.domain.enums import CategoryEnum
from src.domain.message_queues import AbstractMessageQueue
from src.infrastructure.repositories import PostgresRepository
from src.infrastructure.sql.models import Base, Category
from src.representation.routers import get_repository


class InMemoryMessageQueue(AbstractMessageQueue):
    def __init__(self) -> None:
        self.sent_messages: list[bytes] = []
        self.publish_error: Exception | None = None

    async def send_registration_message(self, byte_data: bytes) -> None:
        if self.publish_error is not None:
            raise self.publish_error
        self.sent_messages.append(byte_data)

    async def process_registration_messages(
        self, repo_callback, exchange_rate_awaitable
    ) -> None:
        pass


@pytest.fixture(scope="session")
def postgres() -> Generator[testing.postgresql.Postgresql, None, None]:
    instance = testing.postgresql.Postgresql()
    yield instance
    instance.stop()


@pytest.fixture(scope="session")
def database_url(postgres: testing.postgresql.Postgresql) -> str:
    dsn = postgres.dsn()
    return f"postgresql+asyncpg://{dsn['user']}@{dsn['host']}:{dsn['port']}/{dsn['database']}"


@pytest.fixture
async def engine(database_url: str) -> AsyncGenerator[AsyncEngine, None]:
    eng = create_async_engine(database_url, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield eng

    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest.fixture
async def session_maker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture
async def db_session(
    session_maker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    async with session_maker() as session:
        for uid, category_name in enumerate(CategoryEnum, start=1):
            session.add(Category(uid=uid, category_name=category_name))
        await session.commit()
        yield session
        await session.rollback()


@pytest.fixture
def mock_mq() -> InMemoryMessageQueue:
    return InMemoryMessageQueue()


@pytest.fixture(autouse=True)
def mock_redis_registration_status() -> Generator[None, None, None]:
    with patch(
        "src.infrastructure.sql.units_of_work.get_cached_status",
        AsyncMock(return_value=None),
    ):
        yield


@pytest.fixture
def producer_app(
    db_session: AsyncSession,
    session_maker: async_sessionmaker[AsyncSession],
    mock_mq: InMemoryMessageQueue,
) -> Any:
    from fastapi import FastAPI

    from src.representation.handlers import register_exception_handlers
    from src.representation.middleware import (
        register_middleware,
        register_request_logging,
    )
    from src.representation.routers import get_router, post_router

    app = FastAPI()
    app.state.mq = mock_mq
    register_middleware(app)
    register_exception_handlers(app)
    register_request_logging(app)
    app.include_router(post_router)
    app.include_router(get_router)
    app.dependency_overrides[get_repository] = lambda: PostgresRepository(session_maker)
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
async def api_client(producer_app: Any) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=producer_app, raise_app_exceptions=False)
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


@pytest.fixture
def rabbit_url() -> str:
    url = os.environ.get(
        "TEST_RABBIT_URL",
        "amqp://guest:guest@localhost:5672/",
    )
    return url


@pytest.fixture
async def rabbit_available(rabbit_url: str) -> str:
    from aio_pika import connect

    try:
        connection = await connect(rabbit_url, timeout=2)
    except Exception as exc:
        pytest.skip(f"RabbitMQ not available at {rabbit_url}: {exc}")
    await connection.close()
    return rabbit_url
