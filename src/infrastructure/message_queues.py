from json import loads as json_loads

from aio_pika import DeliveryMode, connect
from aio_pika import Message as AQMessage
from aio_pika.abc import (
    AbstractChannel,
    AbstractConnection,
    AbstractQueue,
)

from src.core.logging import logger
from src.domain.message_queues import AbstractMessageQueuePublisher
from src.infrastructure.redis.reg_status import cache_status


class RabbitMessageQueuePublisher(AbstractMessageQueuePublisher):
    def __init__(self, url: str) -> None:
        """
        don't call like this, await RabbitMessageQueuePublisher.create(url) instead
        """
        self._url: str = url
        self.connection: AbstractConnection
        self._channel: AbstractChannel
        self._queue: AbstractQueue

    @classmethod
    async def create(cls, url: str) -> RabbitMessageQueuePublisher:
        instance = RabbitMessageQueuePublisher(url)
        instance.connection = await connect(instance._url)
        instance._channel = await instance.connection.channel()
        instance._queue = await instance._channel.declare_queue("hello", durable=True)
        logger.info(f"Connected to RabbitMQ queue={instance._queue.name}")
        return instance

    async def send_registration_message(self, byte_data: bytes) -> None:
        data = json_loads(byte_data.decode())
        uid, session_id = data["uid"], data["session_id"]
        # send to redis as 'pending'
        await cache_status(uid, session_id)

        try:
            await self._channel.default_exchange.publish(
                AQMessage(byte_data, delivery_mode=DeliveryMode.PERSISTENT),
                routing_key=self._queue.name,
            )
        except Exception as exc:
            logger.exception(f"Couldn't send package for registration: {exc}")
            raise exc
