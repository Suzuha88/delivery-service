from abc import ABC, abstractmethod
from typing import Any

from src.domain.dataclasses import PackageFilters, PackageRegistrationData


class AbstractRepository(ABC):
    @abstractmethod
    async def register_package(self, package_info: PackageRegistrationData) -> None:
        pass

    @abstractmethod
    async def get_package(self, package_id: str, user_id: str) -> dict[str, Any]:
        pass

    @abstractmethod
    async def get_all_packages(
        self, user_id: str, filters: PackageFilters
    ) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    async def get_all_categories(self) -> list[dict[str, Any]]:
        pass
