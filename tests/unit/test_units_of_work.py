from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.domain.dataclasses import PackageFilters, PackageRegistrationData
from src.domain.enums import CategoryEnum
from src.domain.exceptions import PackageIsPendingError, PackageNotFoundError
from src.infrastructure.sql.models import Category, Package
from src.infrastructure.sql.units_of_work import UnitOfWork


def _registration_data(**overrides: object) -> PackageRegistrationData:
    data = {
        "uid": "pkg-001",
        "session_id": "consumer-session",
        "name": "Headphones",
        "weight": 0.25,
        "dollar_price": 10.0,
        "category_name": CategoryEnum.ELECTRONICS,
        "exchange_rate": 90.0,
    }
    data.update(overrides)
    return PackageRegistrationData(**data)


async def test_register_package_inserts_with_delivery_price(
    session_maker: async_sessionmaker[AsyncSession],
    db_session: AsyncSession,
) -> None:
    await UnitOfWork.register_package(session_maker, _registration_data())

    package = (
        (await db_session.execute(select(Package).where(Package.uid == "pkg-001")))
        .scalars()
        .one()
    )
    assert package.name == "Headphones"
    assert package.delivery_price == pytest.approx(0.25 * 0.5 + 10.0 * 0.01 * 90.0)


async def test_register_package_missing_category_row_raises(
    session_maker: async_sessionmaker[AsyncSession],
    db_session: AsyncSession,
) -> None:
    await db_session.execute(Category.__table__.delete())
    await db_session.commit()

    with pytest.raises(ValueError, match="Unknown category"):
        await UnitOfWork.register_package(session_maker, _registration_data())


async def test_get_package_returns_registered_package(
    session_maker: async_sessionmaker[AsyncSession],
    db_session: AsyncSession,
) -> None:
    category = (
        (
            await db_session.execute(
                select(Category).where(Category.category_name == CategoryEnum.CLOTHES)
            )
        )
        .scalars()
        .one()
    )

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

    result = await UnitOfWork.get_package(session_maker, "existing-pkg", "owner-session")

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
        await UnitOfWork.get_package(session_maker, "missing-pkg", "owner-session")


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
        await UnitOfWork.get_package(session_maker, "missing-pkg", "owner-session")


async def test_get_all_packages_applies_filters(
    session_maker: async_sessionmaker[AsyncSession],
    db_session: AsyncSession,
) -> None:
    electronics = (
        (
            await db_session.execute(
                select(Category).where(
                    Category.category_name == CategoryEnum.ELECTRONICS
                )
            )
        )
        .scalars()
        .one()
    )
    clothes = (
        (
            await db_session.execute(
                select(Category).where(Category.category_name == CategoryEnum.CLOTHES)
            )
        )
        .scalars()
        .one()
    )

    db_session.add_all(
        [
            Package(
                uid="phone",
                session_id="owner-session",
                user_seq=0,
                name="Phone",
                weight=0.3,
                category_id=electronics.uid,
                dollar_price=200.0,
                delivery_price=18.0,
            ),
            Package(
                uid="jacket",
                session_id="owner-session",
                user_seq=1,
                name="Jacket",
                weight=1.0,
                category_id=clothes.uid,
                dollar_price=50.0,
                delivery_price=None,
            ),
        ]
    )
    await db_session.commit()

    packages = await UnitOfWork.get_all_packages(
        session_maker,
        "owner-session",
        PackageFilters(
            start=0,
            limit=10,
            category=CategoryEnum.ELECTRONICS,
            delivery_price_has_been_calculated=True,
        ),
    )

    assert len(packages) == 1
    assert packages[0]["uid"] == "phone"


async def test_get_all_packages_empty_raises(
    session_maker: async_sessionmaker[AsyncSession],
    db_session: AsyncSession,
) -> None:
    with pytest.raises(PackageNotFoundError):
        await UnitOfWork.get_all_packages(
            session_maker,
            "missing-session",
            PackageFilters(
                start=0,
                limit=None,
                category=None,
                delivery_price_has_been_calculated=None,
            ),
        )


async def test_get_all_categories(
    session_maker: async_sessionmaker[AsyncSession],
    db_session: AsyncSession,
) -> None:
    categories = await UnitOfWork.get_all_categories(session_maker)
    assert {item["category_name"] for item in categories} == set(CategoryEnum)
