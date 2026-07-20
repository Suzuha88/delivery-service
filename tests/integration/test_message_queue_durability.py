import json
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from aio_pika import DeliveryMode, Message, connect

from src.infrastructure.message_queues import RabbitMessageQueue

pytestmark = pytest.mark.integration


async def _connect_queue(rabbit_url: str, queue_name: str):
    connection = await connect(rabbit_url)
    channel = await connection.channel()
    queue = await channel.declare_queue(queue_name, durable=True)
    return connection, channel, queue


async def test_durable_queue_retains_message_after_connection_close(
    rabbit_available: str,
) -> None:
    queue_name = f"test_durable_{uuid.uuid4().hex}"
    payload = {"event": "registration", "uid": "durability-test"}

    connection, channel, queue = await _connect_queue(rabbit_available, queue_name)
    await channel.default_exchange.publish(
        Message(
            json.dumps(payload).encode(),
            delivery_mode=DeliveryMode.PERSISTENT,
        ),
        routing_key=queue.name,
    )
    await connection.close()

    connection, channel, queue = await _connect_queue(rabbit_available, queue_name)
    message = await queue.get(timeout=5, fail=False)
    assert message is not None
    assert json.loads(message.body.decode()) == payload
    await message.ack()
    await connection.close()

    connection = await connect(rabbit_available)
    channel = await connection.channel()
    await channel.queue_delete(queue_name)
    await connection.close()


async def test_send_registration_message_survives_broker_reconnect(
    rabbit_available: str,
) -> None:
    queue_name = f"test_mq_send_{uuid.uuid4().hex}"
    body = {
        "uid": "durability-producer",
        "session_id": "session-durability",
        "name": "Parcel",
        "weight": 1.0,
        "category_name": "miscellaneous",
        "dollar_price": 5.0,
    }

    connection, channel, queue = await _connect_queue(rabbit_available, queue_name)
    mq = RabbitMessageQueue.__new__(RabbitMessageQueue)
    mq._url = rabbit_available
    mq.connection = connection
    mq._channel = channel
    mq._queue = queue

    with patch(
        "src.infrastructure.message_queues.cache_status",
        AsyncMock(),
    ):
        await mq.send_registration_message(json.dumps(body).encode())

    await connection.close()

    connection, channel, queue = await _connect_queue(rabbit_available, queue_name)
    message = await queue.get(timeout=5, fail=False)
    assert message is not None
    assert json.loads(message.body.decode())["uid"] == "durability-producer"
    await message.ack()
    await connection.close()

    connection = await connect(rabbit_available)
    channel = await connection.channel()
    await channel.queue_delete(queue_name)
    await connection.close()
