from contextlib import asynccontextmanager
from json import dumps as json_dumps
from secrets import token_hex
from typing import Annotated, Any

import uvicorn
from aio_pika import Connection, Message, connect
from fastapi import Cookie, FastAPI, Request, Response
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


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, port=settings.API_GATEWAY_PORT)


@app.get("/")
async def index(
) -> Any:
    channel = app.state.channel

    await channel.default_exchange.publish(
        Message(b"Hello from producer!"),
        routing_key=app.state.queue.name,
    )


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
