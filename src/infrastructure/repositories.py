from typing import Any

from sqlalchemy.ext.asyncio import async_sessionmaker

from src.domain.repositories import AbstractRepository
from src.infrastructure.sql.units_of_work import (
    get_all_categories,
    get_all_packages,
    get_package,
    register_package,
)


class PostgresRepository(AbstractRepository):
    def __init__(self, session_factory: async_sessionmaker) -> None:
        super().__init__()
        self.session_factory = session_factory

    async def register_package(self, package_info: dict) -> None:
        return await register_package(self.session_factory, package_info)

    async def get_package(self, package_id: str, user_id: str) -> dict[str, Any]:
        return await get_package(self.session_factory, package_id, user_id)

    async def get_all_packages(self, user_id: str) -> list[dict[str, Any]]:
        return await get_all_packages(self.session_factory, user_id)

    async def get_all_categories(self) -> list[dict[str, Any]]:
        return await get_all_categories(self.session_factory)
