from unittest.mock import AsyncMock, patch

import pytest
from shared.rd_cache import rd_cache


@pytest.mark.asyncio
async def test_get_cached_rates_returns_cached_data() -> None:
    rd_client = AsyncMock()
    rd_client.get = AsyncMock(return_value='{"Valute":{}}')

    result = await rd_cache.get_cached_rates(rd_client)

    assert result == '{"Valute":{}}'
    rd_client.get.assert_awaited_once_with(rd_cache.CACHE_KEY)


@pytest.mark.asyncio
async def test_get_cached_rates_miss_returns_none() -> None:
    rd_client = AsyncMock()
    rd_client.get = AsyncMock(return_value=None)

    result = await rd_cache.get_cached_rates(rd_client)

    assert result is None


@pytest.mark.asyncio
async def test_cache_rates_sets_ttl() -> None:
    rd_client = AsyncMock()
    data = '{"Valute":{}}'

    await rd_cache.cache_rates(rd_client, data)

    rd_client.setex.assert_awaited_once_with(
        rd_cache.CACHE_KEY,
        rd_cache.CACHE_TTL,
        data,
    )


@pytest.mark.asyncio
async def test_get_rates_cache_hit_skips_fetch() -> None:
    rd_client = AsyncMock()
    cached = '{"cached": true}'

    with (
        patch.object(rd_cache, "init_redis", AsyncMock(return_value=rd_client)),
        patch.object(rd_cache, "get_cached_rates", AsyncMock(return_value=cached)),
        patch.object(rd_cache, "fetch_rates", AsyncMock()) as fetch_rates,
        patch.object(rd_cache, "cache_rates", AsyncMock()) as cache_rates,
    ):
        result = await rd_cache.get_rates()

    assert result == cached
    fetch_rates.assert_not_awaited()
    cache_rates.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_rates_cache_miss_fetches_and_caches() -> None:
    rd_client = AsyncMock()
    fresh = '{"fresh": true}'

    with (
        patch.object(rd_cache, "init_redis", AsyncMock(return_value=rd_client)),
        patch.object(rd_cache, "get_cached_rates", AsyncMock(return_value=None)),
        patch.object(rd_cache, "fetch_rates", AsyncMock(return_value=fresh)) as fetch_rates,
        patch.object(rd_cache, "cache_rates", AsyncMock()) as cache_rates,
    ):
        result = await rd_cache.get_rates()

    assert result == fresh
    fetch_rates.assert_awaited_once()
    cache_rates.assert_awaited_once_with(rd_client, fresh)
