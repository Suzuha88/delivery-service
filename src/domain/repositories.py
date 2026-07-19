from abc import ABC, abstractmethod
from typing import Any


class AbstractRepository(ABC):
    @abstractmethod
    async def register_package(self, package_info: dict) -> None:
        pass

    @abstractmethod
    async def get_package(self, package_id: str, user_id: str) -> dict[str, Any]:
        pass

    @abstractmethod
    async def get_all_packages(self, user_id: str) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    async def get_all_categories(self) -> list[dict[str, Any]]:
        pass
