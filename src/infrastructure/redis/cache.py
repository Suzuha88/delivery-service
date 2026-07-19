import asyncio

from redis.asyncio import Redis

from src.config import settings
from src.infrastructure.http.cbr import fetch_rub_exchange_rate
from src.logging import logger

CACHE_KEY = "exchange_rates"
CACHE_TTL = 86400  # 24 hours


async def init_redis() -> Redis:
    rd_client = Redis(
        host=settings.REDIS_HOST,
        port=int(settings.REDIS_PORT),
        decode_responses=True,
    )
    await rd_client.ping()
    return rd_client

redis_client = asyncio.run(init_redis())


async def get_cached_rates(redis_client: Redis) -> float | None:
    cached_data: bytes | str | None = await redis_client.get(CACHE_KEY)
    if cached_data:
        logger.debug("Exchange rate cache hit")
        if isinstance(cached_data, bytes):
            cached_data = cached_data.decode()

        return float(cached_data)

    logger.debug("Exchange rate cache miss")
    return None


async def cache_rates(redis_client: Redis, data: float) -> None:
    await redis_client.setex(CACHE_KEY, CACHE_TTL, data)


async def get_exchange_rate() -> float:
    global redis_client
    try:
        cached_rates = await get_cached_rates(redis_client)
        if cached_rates:
            return cached_rates

        fresh_rates = await fetch_rub_exchange_rate()
        await cache_rates(redis_client, fresh_rates)
        logger.info("Fetched and cached fresh exchange rates")
        return fresh_rates
    finally:
        await redis_client.aclose()
