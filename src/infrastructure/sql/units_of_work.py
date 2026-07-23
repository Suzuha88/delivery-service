from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.core.logging import logger
from src.domain.dataclasses import PackageFilters, PackageRegistrationData
from src.domain.enums import CategoryEnum
from src.domain.exceptions import (
    PackageIsPendingError,
    PackageNotFoundError,
)
from src.infrastructure.redis.reg_status import get_cached_status
from src.infrastructure.sql.models import Category, Package
from src.infrastructure.utils import calculate_delivery_price


class UnitOfWork:
    @classmethod
    async def register_package(
        cls,
        session_factory: async_sessionmaker,
        data: PackageRegistrationData,
    ) -> None:
        # Функция агостична к валюте в которой оплачивается доставка,
        # выходим на мировой рынок
        """
        Register package in sql db
        Arguments:
            message_body: json from rabbitmq, converted to python dict
            exchange_rate:  dollar price of valute in which delivery price is calculated
        """
        delivery_price = calculate_delivery_price(
            data.dollar_price, data.exchange_rate, data.weight
        )

        async with session_factory() as db_session:
            category = (
                (
                    await db_session.execute(
                        select(Category).where(
                            Category.category_name == data.category_name
                        )
                    )
                )
                .scalars()
                .one_or_none()
            )

            if category is None:
                raise ValueError(f"Unknown category: {data.category_name}")

            package_obj = Package(
                uid=data.uid,
                session_id=data.session_id,
                name=data.name,
                weight=data.weight,
                dollar_price=data.dollar_price,
                delivery_price=delivery_price,
                category_id=category.uid,
            )
            db_session.add(package_obj)
            await db_session.commit()
            # транзакция коммитится тк у таски своя собственная сессия
            # со своим коннектом и другие транзакции она не трогает
            logger.info(
                f"Registered package name={data.name} \
                        category={data.category_name} delivery_price={delivery_price}"
            )

    @classmethod
    async def get_package(
        cls, session_factory: async_sessionmaker, uid: str, session_id: str
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

    @classmethod
    async def get_all_packages(
        cls,
        session_factory: async_sessionmaker,
        session_id: str,
        filters: PackageFilters,
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
                .where(
                    Package.session_id == session_id, Package.user_seq >= filters.start
                )
            )

            if filters.limit:
                query = query.limit(filters.limit)
            if filters.category:
                query = query.where(Category.category_name == filters.category)
            if isinstance(filters.delivery_price_has_been_calculated, bool):
                if filters.delivery_price_has_been_calculated:
                    query = query.where(Package.delivery_price != None)
                else:
                    query = query.where(Package.delivery_price == None)

            rows = (await db_session.execute(query)).mappings().all()
            if len(rows) == 0:
                raise PackageNotFoundError(multiple=True)
            return [dict(row) for row in rows]

    @classmethod
    async def get_all_categories(
        cls,
        session_factory: async_sessionmaker,
    ) -> list[dict[str, CategoryEnum]]:
        async with session_factory() as db_session:
            categories = (await db_session.execute(select(Category))).scalars().all()
            return [
                {"uid": category.uid, "category_name": category.category_name}
                for category in categories
            ]
