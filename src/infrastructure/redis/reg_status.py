
from src.infrastructure.redis import redis_client
from src.logging import logger

CACHE_TTL = 300  # 5 minutes


def get_cache_key(uid: str, session_id: str) -> str:
    return uid + "+" + session_id


async def cache_status(uid: str, session_id: str) -> None:
    global redis_client
    await redis_client.setex(get_cache_key(uid, session_id), CACHE_TTL, "Pending")


async def get_cached_status(uid: str, session_id: str) -> str | None:
    global redis_client
    cached_status: bytes | str | None = await redis_client.get(
        get_cache_key(uid, session_id)
    )
    if cached_status:
        logger.debug("Package status cache hit")
        if isinstance(cached_status, bytes):
            cached_status = cached_status.decode()
        return cached_status

    logger.debug("Package status cache miss")
    return None
