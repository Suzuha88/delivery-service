import asyncio
from asyncio import sleep

from faststream import FastStream
from faststream.rabbit import RabbitBroker

from src.core.config import rabbit_settings
from src.core.logging import logger
from src.domain.dataclasses import PackageRegistrationData
from src.infrastructure.redis import RedisManager
from src.infrastructure.redis.excange_rate import get_exchange_rate
from src.infrastructure.repositories import PostgresRepository
from src.infrastructure.sql.db import async_session_maker


def get_repo() -> PostgresRepository:
    return PostgresRepository(async_session_maker)


redis_manager = RedisManager()

broker = RabbitBroker(rabbit_settings.rabbit_url)

app = FastStream(broker)


MAX_RETRIES = 3
MULTIPLIER = 2


@app.after_shutdown
async def shutdown() -> None:
    await redis_manager.close()


@broker.subscriber("hello")
async def base_handler(
    message_body: dict,
) -> None:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(
                f"Processing package registration: name={message_body.get('name')}"
            )
            repo = get_repo()
            exchange_rate = await get_exchange_rate()
            await repo.register_package(
                PackageRegistrationData(**message_body, exchange_rate=exchange_rate)
            )
            break

        except Exception:
            if attempt == MAX_RETRIES:
                logger.exception("Failed to process registration message")
                raise

            t = MULTIPLIER**attempt
            logger.exception(
                f"Failed to process registration message, scheduling for retry in {t} seconds"
            )

            await sleep(t)


async def main() -> None:
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
