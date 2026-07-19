from collections.abc import Awaitable, Callable
from json import loads as json_loads

from aio_pika import Message as AQMessage
from aio_pika import connect
from aio_pika.abc import AbstractChannel, AbstractConnection, AbstractQueue

from src.domain.message_queues import AbstractMessageQueue
from src.domain.repositories import AbstractRepository
from src.logging import logger


class RabbitMessageQueue(AbstractMessageQueue):
    def __init__(self, url: str) -> None:
        """
            don't call like this, await RabbitMessageQueue.create(url) instead
        """
        self._url: str = url
        self.connection: AbstractConnection
        self._channel: AbstractChannel
        self._queue: AbstractQueue

    @classmethod
    async def create(cls, url: str) -> RabbitMessageQueue:
        instance = RabbitMessageQueue(url)
        instance.connection = await connect(instance._url)
        instance._channel = await instance.connection.channel()
        instance._queue = await instance._channel \
            .declare_queue("hello", durable=True)
        logger.info(f"Connected to RabbitMQ queue={instance._queue.name}")
        return instance

    async def send_registration_message(self, byte_data: bytes) -> None:
        try:
            await self._channel.default_exchange.publish(
                AQMessage(byte_data),
                routing_key=self._queue.name,
            )
        except Exception as exc:
            logger.exception(f"Couldn't send package for registration: {exc}")
            raise exc

    async def process_registration_messages(
        self,
        repo_callback: Callable[[], AbstractRepository],
        exchange_rate_awaitable: Callable[[], Awaitable[float]]
    ) -> None:
        """
        Stat processing registration messages
        loads data in dict and sends it with exchange rate to repo
        for insertion
        """

        async with self._queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        message_body = json_loads(message.body)
                        logger.info(
                            f"Processing package registration: name={message_body.get("name")}"
                        )
                        repo = repo_callback()
                        exchange_rate = await exchange_rate_awaitable()
                        message_body["exchange_rate"] = exchange_rate
                        await repo.register_package(message_body)

                    except Exception:
                        logger.exception(
                            "Failed to process registration message")
                        raise
