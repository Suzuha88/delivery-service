from unittest.mock import AsyncMock, patch

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.core.consumer import base_handler
from src.domain.enums import CategoryEnum
from src.infrastructure.repositories import PostgresRepository
from src.infrastructure.sql.models import Package


async def test_base_handler_inserts_package(
    db_session: AsyncSession,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    body = {
        "session_id": "consumer-session",
        "uid": "pkg-consumer-1",
        "name": "Headphones",
        "weight": 0.25,
        "category_name": CategoryEnum.ELECTRONICS.value,
        "dollar_price": 10.0,
    }
    repo = PostgresRepository(session_maker)

    with (
        patch("src.core.consumer.get_repo", return_value=repo),
        patch(
            "src.core.consumer.get_exchange_rate",
            AsyncMock(return_value=90.0),
        ),
    ):
        await base_handler(body)

    result = await db_session.execute(
        select(Package).where(Package.session_id == "consumer-session")
    )
    package = result.scalars().one()
    assert package.name == "Headphones"
    assert package.weight == 0.25
    assert package.dollar_price == 10.0
    assert package.delivery_price == 0.25 * 0.5 + 10.0 * 0.01 * 90.0
    assert package.category_id is not None


async def test_base_handler_uses_category(
    db_session: AsyncSession,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    body = {
        "session_id": "clothes-session",
        "uid": "pkg-consumer-2",
        "name": "Socks",
        "weight": 0.1,
        "category_name": CategoryEnum.CLOTHES.value,
        "dollar_price": 5.0,
    }
    repo = PostgresRepository(session_maker)

    with (
        patch("src.core.consumer.get_repo", return_value=repo),
        patch(
            "src.core.consumer.get_exchange_rate",
            AsyncMock(return_value=90.0),
        ),
    ):
        await base_handler(body)

    package = (
        await db_session.execute(
            select(Package).where(Package.session_id == "clothes-session")
        )
    ).scalars().one()

    await db_session.refresh(package, attribute_names=["category"])
    assert package.category.category_name is CategoryEnum.CLOTHES
