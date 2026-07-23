from abc import ABC, abstractmethod


class AbstractMessageQueuePublisher(ABC):
    @abstractmethod
    async def send_registration_message(self, byte_data: bytes) -> None:
        pass
