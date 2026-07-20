from unittest.mock import AsyncMock, patch

from src.infrastructure.redis import excange_rate as exchange_rate


async def test_get_cached_rates_returns_float() -> None:
    redis_client = AsyncMock()
    redis_client.get = AsyncMock(return_value="90.5")

    result = await exchange_rate.get_cached_rates(redis_client)

    assert result == 90.5
    redis_client.get.assert_awaited_once_with(exchange_rate.CACHE_KEY)


async def test_get_cached_rates_miss_returns_none() -> None:
    redis_client = AsyncMock()
    redis_client.get = AsyncMock(return_value=None)

    result = await exchange_rate.get_cached_rates(redis_client)

    assert result is None


async def test_cache_rates_sets_ttl() -> None:
    redis_client = AsyncMock()

    await exchange_rate.cache_rates(redis_client, 91.0)

    redis_client.setex.assert_awaited_once_with(
        exchange_rate.CACHE_KEY,
        exchange_rate.CACHE_TTL,
        91.0,
    )


async def test_get_exchange_rate_cache_hit_skips_fetch() -> None:
    redis_client = AsyncMock()

    with (
        patch.object(
            exchange_rate.RedisManager,
            "get_client",
            AsyncMock(return_value=redis_client),
        ),
        patch.object(
            exchange_rate,
            "get_cached_rates",
            AsyncMock(return_value=88.0),
        ),
        patch.object(
            exchange_rate,
            "fetch_rub_exchange_rate",
            AsyncMock(),
        ) as fetch_rates,
        patch.object(exchange_rate, "cache_rates", AsyncMock()) as cache_rates,
    ):
        result = await exchange_rate.get_exchange_rate()

    assert result == 88.0
    fetch_rates.assert_not_awaited()
    cache_rates.assert_not_awaited()


async def test_get_exchange_rate_cache_miss_fetches_and_caches() -> None:
    redis_client = AsyncMock()

    with (
        patch.object(
            exchange_rate.RedisManager,
            "get_client",
            AsyncMock(return_value=redis_client),
        ),
        patch.object(
            exchange_rate,
            "get_cached_rates",
            AsyncMock(return_value=None),
        ),
        patch.object(
            exchange_rate,
            "fetch_rub_exchange_rate",
            AsyncMock(return_value=92.0),
        ) as fetch_rates,
        patch.object(exchange_rate, "cache_rates", AsyncMock()) as cache_rates,
    ):
        result = await exchange_rate.get_exchange_rate()

    assert result == 92.0
    fetch_rates.assert_awaited_once()
    cache_rates.assert_awaited_once_with(redis_client, 92.0)
