import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aio_pika import DeliveryMode
from aio_pika import Message as AQMessage

from src.infrastructure.message_queues import RabbitMessageQueuePublisher


async def test_create_declares_durable_queue() -> None:
    connection = AsyncMock()
    channel = AsyncMock()
    queue = MagicMock()
    queue.name = "hello"
    connection.channel = AsyncMock(return_value=channel)
    channel.declare_queue = AsyncMock(return_value=queue)

    with patch(
        "src.infrastructure.message_queues.connect", AsyncMock(return_value=connection)
    ):
        mq = await RabbitMessageQueuePublisher.create("amqp://guest:guest@localhost/")

    channel.declare_queue.assert_awaited_once_with("hello", durable=True)
    assert mq._queue is queue


async def test_send_registration_message_caches_pending_status() -> None:
    mq = RabbitMessageQueuePublisher.__new__(RabbitMessageQueuePublisher)
    mq._channel = MagicMock()
    mq._channel.default_exchange.publish = AsyncMock()
    mq._queue = MagicMock()
    mq._queue.name = "hello"

    body = {
        "uid": "pkg-1",
        "session_id": "session-1",
        "name": "Box",
        "weight": 1.0,
        "category_name": "miscellaneous",
        "dollar_price": 10.0,
    }

    with patch(
        "src.infrastructure.message_queues.cache_status",
        AsyncMock(),
    ) as cache_status:
        await mq.send_registration_message(json.dumps(body).encode())

    cache_status.assert_awaited_once_with("pkg-1", "session-1")
    mq._channel.default_exchange.publish.assert_awaited_once()
    published_message = mq._channel.default_exchange.publish.await_args.args[0]
    assert isinstance(published_message, AQMessage)
    assert published_message.delivery_mode is DeliveryMode.PERSISTENT
    assert json.loads(published_message.body.decode()) == body


async def test_send_registration_message_reraises_publish_error() -> None:
    mq = RabbitMessageQueuePublisher.__new__(RabbitMessageQueuePublisher)
    mq._channel = MagicMock()
    mq._channel.default_exchange.publish = AsyncMock(
        side_effect=RuntimeError("broker down")
    )
    mq._queue = MagicMock()
    mq._queue.name = "hello"

    body = {
        "uid": "pkg-1",
        "session_id": "session-1",
        "name": "Box",
        "weight": 1.0,
        "category_name": "miscellaneous",
        "dollar_price": 10.0,
    }

    with (
        patch("src.infrastructure.message_queues.cache_status", AsyncMock()),
        pytest.raises(RuntimeError, match="broker down"),
    ):
        await mq.send_registration_message(json.dumps(body).encode())
