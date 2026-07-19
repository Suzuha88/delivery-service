from abc import ABC, abstractmethod
from typing import Awaitable, Callable

from src.domain.repositories import AbstractRepository


class AbstractMessageQueue(ABC):
    @abstractmethod
    async def send_registration_message(
            self, byte_data: bytes) -> None:
        pass

    @abstractmethod
    async def process_registration_messages(
        self,
            repo_callback: Callable[[], AbstractRepository],
            exchange_rate_awaitable: Callable[[], Awaitable[float]]) -> None:
        pass
