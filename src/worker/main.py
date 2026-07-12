from contextlib import asynccontextmanager
from typing import Annotated, Any

import uvicorn
from aio_pika import connect, queue
from aio_pika.abc import AbstractIncomingMessage
from db.db import initialize_db
from fastapi import Depends, FastAPI
from shared.config import settings


async def process_mesage(message: AbstractIncomingMessage):
    async with message.process():
        print(message.body)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await initialize_db()

    connection = await connect(settings.RABBIT_URL)
    channel = await connection.channel()
    queue = await channel.declare_queue("hello", durable=True)

    await queue.consume(process_mesage)

    app.state.connection = connection
    app.state.channel = channel
    app.state.queue = queue
    yield

    await connection.close()

app = FastAPI(lifespan=lifespan)


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, port=settings.WORKER_PORT)
