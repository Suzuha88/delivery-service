from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from aio_pika import Connection, Message, connect
from fastapi import FastAPI
from schemas.schemas import PackageSchema
from shared.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    connection = await connect(settings.RABBIT_URL)
    channel = await connection.channel()
    queue = await channel.declare_queue("hello", durable=True)

    app.state.connection = connection
    app.state.channel = channel
    app.state.queue = queue
    yield

    await connection.close()

app = FastAPI(lifespan=lifespan)


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, port=settings.API_GATEWAY_PORT)


@app.get("/")
async def register(
) -> Any:
    channel = app.state.channel

    await channel.default_exchange.publish(
        Message(b"Hello from producer!"),
        routing_key=app.state.queue.name,
    )
