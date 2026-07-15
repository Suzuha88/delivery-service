import json
from unittest.mock import AsyncMock, patch

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from shared.db.enums import CategoryEnum
from shared.db.models import Package
from shared.rabbit.rabbit import process_registration_message


async def test_process_registration_message_inserts_package(
    db_session: AsyncSession,
    session_maker: async_sessionmaker[AsyncSession],
    mock_incoming_message,
    sample_rates_json: str,
) -> None:
    body = {
        "session_id": "consumer-session",
        "name": "Headphones",
        "weight": 0.25,
        "category_name": "electronics",
        "dollar_price": 10.0,
    }
    mock_incoming_message.body = json.dumps(body).encode("utf-8")

    with patch(
        "shared.rabbit.rabbit.get_rates",
        AsyncMock(return_value=sample_rates_json),
    ):
        await process_registration_message(
            mock_incoming_message,
            session_maker=session_maker,
        )

    result = await db_session.execute(
        select(Package).where(Package.session_id == "consumer-session")
    )
    package = result.scalars().one()
    assert package.name == "Headphones"
    assert package.weight == 0.25
    assert package.dollar_price == 10.0
    assert package.ruble_price == 900.0
    assert package.category_id is not None


async def test_process_registration_message_uses_category(
    db_session: AsyncSession,
    session_maker: async_sessionmaker[AsyncSession],
    mock_incoming_message,
    sample_rates_json: str,
) -> None:
    body = {
        "session_id": "clothes-session",
        "name": "Socks",
        "weight": 0.1,
        "category_name": CategoryEnum.CLOTHES.value,
        "dollar_price": 5.0,
    }
    mock_incoming_message.body = json.dumps(body).encode("utf-8")

    with patch(
        "shared.rabbit.rabbit.get_rates",
        AsyncMock(return_value=sample_rates_json),
    ):
        await process_registration_message(
            mock_incoming_message,
            session_maker=session_maker,
        )

    package = (
        await db_session.execute(
            select(Package).where(Package.session_id == "clothes-session")
        )
    ).scalars().one()

    await db_session.refresh(package, attribute_names=["category"])
    assert package.category.category_name is CategoryEnum.CLOTHES
