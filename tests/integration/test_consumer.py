import json
from unittest.mock import AsyncMock, patch

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.domain.enums import CategoryEnum
from src.infrastructure.message_queues import RabbitMessageQueue
from src.infrastructure.sql.models import Package


async def test_process_registration_message_inserts_package(
    db_session: AsyncSession,
    session_maker: async_sessionmaker[AsyncSession],
    mock_incoming_message,
) -> None:
    body = {
        "session_id": "consumer-session",
        "uid": "pkg-consumer-1",
        "name": "Headphones",
        "weight": 0.25,
        "category_name": CategoryEnum.ELECTRONICS.value,
        "dollar_price": 10.0,
    }
    mock_incoming_message.body = json.dumps(body).encode("utf-8")

    mq = RabbitMessageQueue.__new__(RabbitMessageQueue)

    async def one_message_iter():
        yield mock_incoming_message

    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def iterator():
        yield one_message_iter()

    mq._queue = AsyncMock()
    mq._queue.iterator = iterator

    from src.infrastructure.repositories import PostgresRepository

    repo = PostgresRepository(session_maker)

    with patch(
        "src.infrastructure.sql.units_of_work.get_cached_status",
        AsyncMock(return_value=None),
    ):
        await mq.process_registration_messages(
            repo_callback=lambda: repo,
            exchange_rate_awaitable=AsyncMock(return_value=90.0),
        )

    result = await db_session.execute(
        select(Package).where(Package.session_id == "consumer-session")
    )
    package = result.scalars().one()
    assert package.name == "Headphones"
    assert package.weight == 0.25
    assert package.dollar_price == 10.0
    assert package.delivery_price == 0.25 * 0.5 + 10.0 * 90.0
    assert package.category_id is not None


async def test_process_registration_message_uses_category(
    db_session: AsyncSession,
    session_maker: async_sessionmaker[AsyncSession],
    mock_incoming_message,
) -> None:
    body = {
        "session_id": "clothes-session",
        "uid": "pkg-consumer-2",
        "name": "Socks",
        "weight": 0.1,
        "category_name": CategoryEnum.CLOTHES.value,
        "dollar_price": 5.0,
    }
    mock_incoming_message.body = json.dumps(body).encode("utf-8")

    mq = RabbitMessageQueue.__new__(RabbitMessageQueue)

    async def one_message_iter():
        yield mock_incoming_message

    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def iterator():
        yield one_message_iter()

    mq._queue = AsyncMock()
    mq._queue.iterator = iterator

    from src.infrastructure.repositories import PostgresRepository

    repo = PostgresRepository(session_maker)

    with patch(
        "src.infrastructure.sql.units_of_work.get_cached_status",
        AsyncMock(return_value=None),
    ):
        await mq.process_registration_messages(
            repo_callback=lambda: repo,
            exchange_rate_awaitable=AsyncMock(return_value=90.0),
        )

    package = (
        await db_session.execute(
            select(Package).where(Package.session_id == "clothes-session")
        )
    ).scalars().one()

    await db_session.refresh(package, attribute_names=["category"])
    assert package.category.category_name is CategoryEnum.CLOTHES
