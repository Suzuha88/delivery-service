from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.domain.enums import CategoryEnum
from src.domain.exceptions import PackageIsPendingError, PackageNotFoundError
from src.infrastructure.sql.models import Category, Package
from src.infrastructure.sql.units_of_work import get_package, register_package


async def test_register_package_inserts_with_delivery_price(
    session_maker: async_sessionmaker[AsyncSession],
    db_session: AsyncSession,
) -> None:
    body = {
        "session_id": "consumer-session",
        "uid": "pkg-001",
        "name": "Headphones",
        "weight": 0.25,
        "category_name": CategoryEnum.ELECTRONICS,
        "dollar_price": 10.0,
        "exchange_rate": 90.0,
    }

    await register_package(session_maker, body.copy())

    package = (
        await db_session.execute(
            select(Package).where(Package.uid == "pkg-001")
        )
    ).scalars().one()
    assert package.name == "Headphones"
    assert package.delivery_price == pytest.approx(0.25 * 0.5 + 10.0 * 90.0)


async def test_get_package_returns_registered_package(
    session_maker: async_sessionmaker[AsyncSession],
    db_session: AsyncSession,
) -> None:
    category = (
        await db_session.execute(
            select(Category).where(Category.category_name == CategoryEnum.CLOTHES)
        )
    ).scalars().one()

    package = Package(
        uid="existing-pkg",
        session_id="owner-session",
        user_seq=0,
        name="Jacket",
        weight=1.0,
        category_id=category.uid,
        dollar_price=50.0,
        delivery_price=4500.0,
    )
    db_session.add(package)
    await db_session.commit()

    result = await get_package(session_maker, "existing-pkg", "owner-session")

    assert result["name"] == "Jacket"
    assert result["category"] is CategoryEnum.CLOTHES


async def test_get_package_pending_raises(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    with (
        patch(
            "src.infrastructure.sql.units_of_work.get_cached_status",
            AsyncMock(return_value="Pending"),
        ),
        pytest.raises(PackageIsPendingError),
    ):
        await get_package(session_maker, "missing-pkg", "owner-session")


async def test_get_package_not_found_raises(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    with (
        patch(
            "src.infrastructure.sql.units_of_work.get_cached_status",
            AsyncMock(return_value=None),
        ),
        pytest.raises(PackageNotFoundError),
    ):
        await get_package(session_maker, "missing-pkg", "owner-session")
