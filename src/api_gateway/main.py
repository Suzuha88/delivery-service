from contextlib import asynccontextmanager
from json import dumps as json_dumps
from secrets import token_hex
from typing import AsyncGenerator

import uvicorn
from aio_pika import Message
from fastapi import FastAPI, Request, Response, status
from schemas.schemas import PackageSchema
from shared.config import settings
from shared.db import initialize_db
from shared.rabbit import initialize_rabbitmq
from starlette.middleware.base import RequestResponseEndpoint

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, port=settings.API_GATEWAY_PORT)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    await initialize_db()
    connection, channel, queue = await initialize_rabbitmq()

    app.state.connection = connection
    app.state.channel = channel
    app.state.queue = queue
    yield

    await connection.close()

app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def add_session_id(
    request: Request,
    call_next: RequestResponseEndpoint
) -> None | Response:
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

) -> Response:

    session_id = request.cookies.get(
        "session_id") or request.state.session_id

    channel = app.state.channel
    dict_body = package.model_dump()

    dict_body["session_id"] = session_id

    byte_body = json_dumps(dict_body).encode("utf-8")

    try:
        await channel.default_exchange.publish(
            Message(byte_body),
            routing_key=app.state.queue.name
        )
        return Response(content={"message": "Package sent for registration"},
                        status_code=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            content={"error": f"Couldn't send package for registration: {e}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
