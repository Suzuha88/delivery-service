from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI
from shared.db import initialize_db
from shared.rabbit import initialize_rabbitmq, process_registration_message

from shared import settings

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, port=settings.WORKER_PORT)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    await initialize_db()

    connection, channel, queue = await initialize_rabbitmq()

    await queue.consume(process_registration_message)

    app.state.connection = connection
    app.state.channel = channel
    app.state.queue = queue
    yield

    await connection.close()

app = FastAPI(lifespan=lifespan)
