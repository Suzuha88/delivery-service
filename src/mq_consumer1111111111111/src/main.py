from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI
from shared.config import settings
from shared.fastapi_utils import register_exception_handlers, register_request_logging
from shared.rabbit import initialize_rabbitmq, process_registration_message


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    connection, channel, queue = await initialize_rabbitmq()
    await queue.consume(process_registration_message)

    app.state.connection = connection
    app.state.channel = channel
    app.state.queue = queue
    yield

    await connection.close()


app = FastAPI(lifespan=lifespan)
register_exception_handlers(app)
register_request_logging(app)


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, port=settings.MQ_CONSUMER_PORT)
