from unittest.mock import AsyncMock, patch

from src.infrastructure.redis import reg_status


async def test_cache_status_sets_pending_with_ttl() -> None:
    redis_client = AsyncMock()

    with patch.object(
        reg_status.RedisManager,
        "get_client",
        AsyncMock(return_value=redis_client),
    ):
        await reg_status.cache_status("uid-1", "session-1")

    redis_client.setex.assert_awaited_once_with(
        "uid-1+session-1",
        reg_status.CACHE_TTL,
        "Pending",
    )


async def test_get_cached_status_returns_decoded_value() -> None:
    redis_client = AsyncMock()
    redis_client.get = AsyncMock(return_value=b"Pending")

    with patch.object(
        reg_status.RedisManager,
        "get_client",
        AsyncMock(return_value=redis_client),
    ):
        result = await reg_status.get_cached_status("uid-1", "session-1")

    assert result == "Pending"


async def test_get_cached_status_miss_returns_none() -> None:
    redis_client = AsyncMock()
    redis_client.get = AsyncMock(return_value=None)

    with patch.object(
        reg_status.RedisManager,
        "get_client",
        AsyncMock(return_value=redis_client),
    ):
        result = await reg_status.get_cached_status("uid-1", "session-1")

    assert result is None
