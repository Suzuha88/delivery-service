from asyncio import Lock

from redis.asyncio import Redis

from src.core.config import redis_settings as settings


class RedisManager:
    _instance: RedisManager | None = None
    _client: Redis | None = None
    _lock = Lock()

    def __new__(cls) -> RedisManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def get_client(self) -> Redis:
        if self._client is None:
            async with self._lock:
                if self._client is None:
                    self._client = Redis(
                        host=settings.REDIS_HOST,
                        port=settings.REDIS_PORT,
                        decode_responses=True,
                    )
                    await self._client.ping()

        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None
