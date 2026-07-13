
from datetime import datetime
from json import loads

from aiohttp import ClientSession
from redis.asyncio import Redis

from shared import settings

CACHE_KEY = "exchange_rates"
CACHE_TTL = 86400  # 24 hours


async def init_redis() -> Redis:
    rd_client = Redis(port=settings.REDIS_PORT, decode_responses=True)

    await rd_client.ping()
    return rd_client


async def get_cached_rates(rd_client: Redis):
    cached_data = await rd_client.get(CACHE_KEY)

    if cached_data:
        print("Cache hit")

        return cached_data

    print("Cache miss - no data")


async def fetch_rates():
    async with ClientSession() as session, \
            session.get("https://www.cbr-xml-daily.ru/daily_json.js") as resp:

        data = await resp.text()

        return data


async def cache_rates(rd_client: Redis, data):
    await rd_client.setex(
        CACHE_KEY,
        CACHE_TTL,
        data
    )


async def get_rates():

    rd_client = await init_redis()

    cached_rates = await get_cached_rates(rd_client)

    if not cached_rates:
        fresh_rates = await fetch_rates()
        await cache_rates(rd_client, fresh_rates)

        return fresh_rates

    return cached_rates
