from contextlib import asynccontextmanager
from json import dumps as json_dumps
from secrets import token_hex
from typing import Annotated, Any, AsyncGenerator

import uvicorn
from aio_pika import Message as AQMessage
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from loguru import logger
from shared.config import settings
from shared.db import get_session, initialize_db
from shared.db.models import Category, Package
from shared.fastapi_utils import register_exception_handlers, register_request_logging
from shared.rabbit import initialize_rabbitmq
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import RequestResponseEndpoint

from schemas.schemas import CategoryResponse, PackageResponse, PackageSchema
from utils import get_session_id


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.level(settings.LOG_LEVEL)
    await initialize_db()  # run migrations, popilate categories table
    connection, channel, queue = await initialize_rabbitmq()

    app.state.connection = connection
    app.state.channel = channel
    app.state.queue = queue
    yield

    await connection.close()


app = FastAPI(lifespan=lifespan)
register_exception_handlers(app)
register_request_logging(app)


@app.middleware("http")
async def add_session_id(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    """
    Check if request has session id, if not
    Forward it with state variable of same name, get response and set session id
    """
    session_id = request.cookies.get("session_id")

    if not session_id:
        session_id = request.state.session_id = token_hex(16)
        response = await call_next(request)
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=True,
        )
        return response

    return await call_next(request)


@app.post("/register")
async def register(
    package: PackageSchema,
    request: Request,
) -> dict[str, str]:
    """Send package info for registration into message queue"""
    session_id = get_session_id(request)
    channel = app.state.channel
    dict_body = package.model_dump(mode="json")
    dict_body["session_id"] = session_id
    byte_body = json_dumps(dict_body).encode("utf-8")

    try:
        await channel.default_exchange.publish(
            AQMessage(byte_body),
            routing_key=app.state.queue.name,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't send package for registration: {exc}",
        ) from exc

    return {"message": "Package sent for registration"}


@app.get("/packages/{package_id}", response_model=PackageResponse)
async def get_package(
    request: Request,
    db_session: Annotated[AsyncSession, Depends(get_session)],
    package_id: int,
) -> dict[str, Any]:
    """
    Get package of same user by id
    Even if id exists will not return package of other user
    """
    session_id = get_session_id(request)
    query = select(
        Package.uid,
        Package.name,
        Package.weight,
        Package.dollar_price,
        Package.ruble_price,
        Category.category_name.label("category"),
    ).join(Package.category).where(
        Package.session_id == session_id,
        Package.uid == package_id,
    )

    res = (await db_session.execute(query)).mappings().one_or_none()
    if res is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No packages with this id",
        )
    return dict(res)


@app.get("/packages", response_model=list[PackageResponse])
async def get_all_packages(
    request: Request,
    db_session: Annotated[AsyncSession, Depends(get_session)],
) -> list[dict[str, Any]]:
    """Get all packages"""
    session_id = get_session_id(request)
    query = select(
        Package.uid,
        Package.name,
        Package.weight,
        Package.dollar_price,
        Package.ruble_price,
        Category.category_name.label("category"),
    ).join(Package.category).where(Package.session_id == session_id)

    rows = (await db_session.execute(query)).mappings().all()
    return [dict(row) for row in rows]


@app.get("/categories", response_model=list[CategoryResponse])
async def get_all_categories(
    db_session: Annotated[AsyncSession, Depends(get_session)],
) -> list[dict[str, Any]]:
    """Get all categories"""
    categories = (await db_session.execute(select(Category))).scalars().all()
    return [
        {"uid": category.uid, "category_name": category.category_name}
        for category in categories
    ]


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, port=settings.API_GATEWAY_PORT)
