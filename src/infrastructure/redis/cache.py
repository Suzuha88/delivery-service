import asyncio

from redis.asyncio import Redis

from src.config import settings


async def init_redis() -> Redis:
    rd_client = Redis(
        host=settings.REDIS_HOST,
        port=int(settings.REDIS_PORT),
        decode_responses=True,
    )
    await rd_client.ping()
    return rd_client


redis_client = asyncio.run(init_redis())
