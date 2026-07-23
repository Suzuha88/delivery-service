from typing import Any

from sqlalchemy.ext.asyncio import async_sessionmaker

from src.domain.dataclasses import PackageFilters, PackageRegistrationData
from src.domain.repositories import AbstractRepository
from src.infrastructure.sql.units_of_work import UnitOfWork


class PostgresRepository(AbstractRepository):
    def __init__(self, session_factory: async_sessionmaker) -> None:
        super().__init__()
        self.session_factory = session_factory

    async def register_package(self, package_info: PackageRegistrationData) -> None:
        return await UnitOfWork.register_package(self.session_factory, package_info)

    async def get_package(self, package_id: str, user_id: str) -> dict[str, Any]:
        return await UnitOfWork.get_package(self.session_factory, package_id, user_id)

    async def get_all_packages(
        self, user_id: str, filters: PackageFilters
    ) -> list[dict[str, Any]]:
        return await UnitOfWork.get_all_packages(
            self.session_factory,
            user_id,
            filters,
        )

    async def get_all_categories(self) -> list[dict[str, Any]]:
        return await UnitOfWork.get_all_categories(self.session_factory)
