from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI

from src.core.config import consumer_settings, rabbit_settings
from src.infrastructure.http.cbr import fetch_rub_exchange_rate
from src.infrastructure.message_queues import RabbitMessageQueue
from src.infrastructure.redis.cache import RedisManager
from src.infrastructure.repositories import PostgresRepository
from src.infrastructure.sql.db import async_session_maker
from src.representation.handlers import register_exception_handlers
from src.representation.middleware import register_request_logging


def get_repo() -> PostgresRepository:
    return PostgresRepository(async_session_maker)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    rabbit = await RabbitMessageQueue.create(rabbit_settings.rabbit_url)
    await rabbit.process_registration_messages(get_repo, fetch_rub_exchange_rate)
    app.state.mq = rabbit

    yield

    rm = RedisManager()
    await rm.close()
    await app.state.mq.connection.close()


def setup_consumer() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    register_exception_handlers(app)
    register_request_logging(app)
    return app


app = setup_consumer()


if __name__ == "__main__":
    uvicorn.run("consumer:app", reload=True, port=consumer_settings.CONSUMER_PORT)
