import json
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest
from aio_pika import DeliveryMode, Message as AQMessage

from src.infrastructure.message_queues import RabbitMessageQueue


def _make_mq_with_message(body: dict) -> tuple[RabbitMessageQueue, MagicMock, AsyncMock]:
    message = MagicMock()
    message.body = json.dumps(body).encode()

    @asynccontextmanager
    async def process(**_kwargs: object):
        yield

    message.process = process

    async def queue_iter():
        yield message

    @asynccontextmanager
    async def iterator():
        yield queue_iter()

    mq = RabbitMessageQueue.__new__(RabbitMessageQueue)
    mq._queue = MagicMock()
    mq._queue.iterator = iterator
    repo = AsyncMock()
    return mq, message, repo


async def test_create_declares_durable_queue() -> None:
    connection = AsyncMock()
    channel = AsyncMock()
    queue = MagicMock()
    queue.name = "hello"
    connection.channel = AsyncMock(return_value=channel)
    channel.declare_queue = AsyncMock(return_value=queue)

    with patch("src.infrastructure.message_queues.connect", AsyncMock(return_value=connection)):
        mq = await RabbitMessageQueue.create("amqp://guest:guest@localhost/")

    channel.declare_queue.assert_awaited_once_with("hello", durable=True)
    assert mq._queue is queue


async def test_send_registration_message_caches_pending_status() -> None:
    mq = RabbitMessageQueue.__new__(RabbitMessageQueue)
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
    mq = RabbitMessageQueue.__new__(RabbitMessageQueue)
    mq._channel = MagicMock()
    mq._channel.default_exchange.publish = AsyncMock(side_effect=RuntimeError("broker down"))
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


async def test_process_registration_message_registers_package() -> None:
    body = {
        "session_id": "consumer-session",
        "uid": "pkg-uid",
        "name": "Headphones",
        "weight": 0.25,
        "category_name": "electronics",
        "dollar_price": 10.0,
    }

    mq, _, repo = _make_mq_with_message(body)

    await mq.process_registration_messages(
        repo_callback=lambda: repo,
        exchange_rate_awaitable=AsyncMock(return_value=90.0),
    )

    repo.register_package.assert_awaited_once()
    registered = repo.register_package.await_args.args[0]
    assert registered["exchange_rate"] == 90.0
    assert registered["name"] == "Headphones"
    assert registered["session_id"] == "consumer-session"


async def test_process_registration_message_uses_requeue() -> None:
    body = {
        "session_id": "consumer-session",
        "uid": "pkg-uid",
        "name": "Headphones",
        "weight": 0.25,
        "category_name": "electronics",
        "dollar_price": 10.0,
    }

    message = MagicMock()
    message.body = json.dumps(body).encode()
    process_kwargs: list[dict[str, object]] = []

    @asynccontextmanager
    async def process(**kwargs: object):
        process_kwargs.append(dict(kwargs))
        yield

    message.process = process

    async def queue_iter():
        yield message

    @asynccontextmanager
    async def iterator():
        yield queue_iter()

    mq = RabbitMessageQueue.__new__(RabbitMessageQueue)
    mq._queue = MagicMock()
    mq._queue.iterator = iterator
    repo = AsyncMock()

    await mq.process_registration_messages(
        repo_callback=lambda: repo,
        exchange_rate_awaitable=AsyncMock(return_value=90.0),
    )

    assert process_kwargs == [{"requeue": True}]


async def test_process_registration_message_retries_before_success() -> None:
    body = {
        "session_id": "consumer-session",
        "uid": "pkg-uid",
        "name": "Headphones",
        "weight": 0.25,
        "category_name": "electronics",
        "dollar_price": 10.0,
    }

    mq, _, repo = _make_mq_with_message(body)
    repo.register_package = AsyncMock(
        side_effect=[RuntimeError("db down"), RuntimeError("db down"), None]
    )

    with patch("src.infrastructure.message_queues.sleep", AsyncMock()) as sleep_mock:
        await mq.process_registration_messages(
            repo_callback=lambda: repo,
            exchange_rate_awaitable=AsyncMock(return_value=90.0),
            max_retries=3,
            multiplier=2,
        )

    assert repo.register_package.await_count == 3
    sleep_mock.assert_has_awaits([call(2), call(4)])


async def test_process_registration_message_raises_after_max_retries() -> None:
    body = {
        "session_id": "consumer-session",
        "uid": "pkg-uid",
        "name": "Headphones",
        "weight": 0.25,
        "category_name": "electronics",
        "dollar_price": 10.0,
    }

    mq, _, repo = _make_mq_with_message(body)
    repo.register_package = AsyncMock(side_effect=RuntimeError("db down"))

    with (
        patch("src.infrastructure.message_queues.sleep", AsyncMock()) as sleep_mock,
        pytest.raises(RuntimeError, match="db down"),
    ):
        await mq.process_registration_messages(
            repo_callback=lambda: repo,
            exchange_rate_awaitable=AsyncMock(return_value=90.0),
            max_retries=3,
            multiplier=2,
        )

    assert repo.register_package.await_count == 3
    sleep_mock.assert_has_awaits([call(2), call(4)])
