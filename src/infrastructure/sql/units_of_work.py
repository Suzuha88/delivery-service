from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.domain.enums import CategoryEnum
from src.domain.exceptions import (
    PackageIsPendingError,
    PackageNotFoundError,
)
from src.infrastructure.redis.reg_status import get_cached_status
from src.infrastructure.sql.models import Category, Package
from src.infrastructure.utils import calculate_delivery_price
from src.logging import logger


async def register_package(
    session_factory: async_sessionmaker,
    message_body: dict,
) -> None:
    # Функция агостична к валюте в которой оплачивается доставка,
    # выходим на мировой рынок
    """
    Register package in sql db
    Arguments:
        message_body: json from rabbitmq, converted to python dict
        exchange_rate:  dollar price of valute in which delivery price is calculated
    """
    category_name = message_body.pop("category_name")
    package_name = message_body["name"]
    dollar_price = message_body["dollar_price"]
    weight = message_body["weight"]
    exchange_rate = message_body.pop("exchange_rate")
    delivery_price = calculate_delivery_price(dollar_price, exchange_rate, weight)

    async with session_factory() as db_session:
        category = (
            (
                await db_session.execute(
                    select(Category).where(Category.category_name == category_name)
                )
            )
            .scalars()
            .one_or_none()
        )

        if category is None:
            raise ValueError(f"Unknown category: {category_name}")

        package_obj = Package(
            **message_body,
            delivery_price=delivery_price,
            category_id=category.uid,
        )
        db_session.add(package_obj)
        await db_session.commit()
        # транзакция коммитится тк у таски своя собственная сессия
        # со своим коннектом и другие транзакции она не трогает
        logger.info(
            f"Registered package name={package_name} \
                    category={category_name} delivery_price={delivery_price}"
        )


async def get_package(
    session_factory: async_sessionmaker, uid: str, session_id: str
) -> dict[str, Any]:
    async with session_factory() as db_session:
        query = (
            select(
                Package.uid,
                Package.name,
                Package.weight,
                Package.dollar_price,
                Package.delivery_price,
                Category.category_name.label("category"),
            )
            .join(Package.category)
            .where(
                Package.session_id == session_id,
                Package.uid == uid,
            )
        )

        res = (await db_session.execute(query)).mappings().one_or_none()
        if res:
            return dict(res)

        elif await get_cached_status(uid, session_id):
            raise PackageIsPendingError()
        else:
            raise PackageNotFoundError()


async def get_all_packages(
    session_factory: async_sessionmaker,
    session_id: str,
    start: int = 0,
    limit: int | None = None,
    category: CategoryEnum | None = None,
    delivery_price_has_been_calculated: bool | None = None,
) -> list[dict[str, Any]]:
    async with session_factory() as db_session:
        query = (
            select(
                Package.uid,
                Package.name,
                Package.weight,
                Package.dollar_price,
                Package.delivery_price,
                Category.category_name.label("category"),
            )
            .join(Package.category)
            .where(Package.session_id == session_id, Package.user_seq >= start)
        )

        if limit:
            query = query.limit(limit)
        if category:
            query = query.where(Category.category_name == category)
        if isinstance(delivery_price_has_been_calculated, bool):
            if delivery_price_has_been_calculated:
                query = query.where(Package.delivery_price != None)
            else:
                query = query.where(Package.delivery_price == None)

        rows = (await db_session.execute(query)).mappings().all()
        if len(rows) == 0:
            raise PackageNotFoundError(multiple=True)
        return [dict(row) for row in rows]


async def get_all_categories(
    session_factory: async_sessionmaker,
) -> list[dict[str, CategoryEnum]]:
    async with session_factory() as db_session:
        categories = (await db_session.execute(select(Category))).scalars().all()
        return [
            {"uid": category.uid, "category_name": category.category_name}
            for category in categories
        ]
