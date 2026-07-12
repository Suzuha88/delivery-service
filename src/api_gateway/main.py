from contextlib import asynccontextmanager
from json import dumps as json_dumps
from secrets import token_hex
from typing import Annotated, Any

import uvicorn
from aio_pika import Message
from fastapi import FastAPI, Request, Response
from schemas.schemas import PackageSchema
from shared.config import settings
from shared.db import initialize_db
from shared.rabbit import initialize_rabbitmq

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, port=settings.API_GATEWAY_PORT)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await initialize_db()
    connection, channel, queue = await initialize_rabbitmq()

    app.state.connection = connection
    app.state.channel = channel
    app.state.queue = queue
    yield

    await connection.close()

app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def add_session_id(request: Request, call_next) -> None | Response:
    session_id = request.cookies.get("session_id")

    if not session_id:

        session_id = request.state.session_id = token_hex(16)
        response: Response = await call_next(request)
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=True
        )

        return response

    response = await call_next(request)
    return response


@app.post("/register")
async def register(
        package: PackageSchema,
        request: Request,

) -> Any:

    session_id = request.cookies.get("session_id") or request.state.session_id

    channel = app.state.channel
    dict_body = package.model_dump()

    dict_body["session_id"] = session_id

    byte_body = json_dumps(dict_body).encode("utf-8")

    await channel.default_exchange.publish(
        Message(byte_body),
        routing_key=app.state.queue.name
    )
