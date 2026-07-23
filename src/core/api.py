from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI

from src.core.config import api_settings, rabbit_settings
from src.infrastructure.message_queues import RabbitMessageQueuePublisher
from src.infrastructure.redis import RedisManager
from src.infrastructure.repositories import PostgresRepository
from src.infrastructure.sql.db import async_session_maker
from src.representation.handlers import register_exception_handlers
from src.representation.middleware import register_middleware, register_request_logging
from src.representation.routers import get_repository, get_router, post_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:

    redis_manager = RedisManager()
    rabbit = await RabbitMessageQueuePublisher.create(rabbit_settings.rabbit_url)
    # Здесь меняется реализация очереди сообщений
    app.state.mq = rabbit

    yield

    await redis_manager.close()

    await app.state.mq.connection.close()


def setup_api() -> FastAPI:

    app = FastAPI(lifespan=lifespan)
    register_middleware(app)
    register_exception_handlers(app)
    register_request_logging(app)

    app.include_router(post_router)
    app.include_router(get_router)

    def get_apg_repository() -> PostgresRepository:
        return PostgresRepository(async_session_maker)

    # Здесь меняется реализация базы данных
    app.dependency_overrides[get_repository] = get_apg_repository

    return app


app = setup_api()

if __name__ == "__main__":
    uvicorn.run("api:app", reload=True, port=api_settings.api_PORT)
