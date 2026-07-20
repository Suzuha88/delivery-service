from abc import ABC, abstractmethod
from typing import Any

from src.domain.enums import CategoryEnum


class AbstractRepository(ABC):
    @abstractmethod
    async def register_package(self, package_info: dict) -> None:
        pass

    @abstractmethod
    async def get_package(self, package_id: str, user_id: str) -> dict[str, Any]:
        pass

    @abstractmethod
    async def get_all_packages(
        self,
        user_id: str,
        start: int = 0,
        limit: int | None = None,
        category: CategoryEnum | None = None,
        delivery_price_has_been_calculated: bool | None = None,
    ) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    async def get_all_categories(self) -> list[dict[str, Any]]:
        pass
