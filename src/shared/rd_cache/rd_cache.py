from aiohttp import ClientSession
from redis.asyncio import Redis

from ..config import settings
from ..logging import logger

CACHE_KEY = "exchange_rates"
CACHE_TTL = 86400  # 24 hours
CBR_RATES_URL = "https://www.cbr-xml-daily.ru/daily_json.js"


async def init_redis() -> Redis:
    rd_client = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=True,
    )
    await rd_client.ping()
    return rd_client


async def get_cached_rates(rd_client: Redis) -> str | None:
    cached_data = await rd_client.get(CACHE_KEY)
    if cached_data:
        logger.debug("Exchange rate cache hit")
        return cached_data

    logger.debug("Exchange rate cache miss")
    return None


async def fetch_rates() -> str:
    async with ClientSession() as session, session.get(CBR_RATES_URL) as resp:
        resp.raise_for_status()
        return await resp.text()


async def cache_rates(rd_client: Redis, data: str) -> None:
    await rd_client.setex(CACHE_KEY, CACHE_TTL, data)


async def get_rates() -> str:
    rd_client = await init_redis()
    try:
        cached_rates = await get_cached_rates(rd_client)
        if cached_rates:
            return cached_rates

        fresh_rates = await fetch_rates()
        await cache_rates(rd_client, fresh_rates)
        logger.info("Fetched and cached fresh exchange rates")
        return fresh_rates
    finally:
        await rd_client.aclose()
