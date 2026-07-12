from contextlib import asynccontextmanager
from json import loads as json_loads
from typing import Annotated, Any, AsyncGenerator

import uvicorn
from aio_pika import connect, queue
from aio_pika.abc import AbstractIncomingMessage
from aiohttp import ClientSession
from db.db import AsyncSessionMaker, initialize_db
from fastapi import Depends, FastAPI
from models.models import Category, Package
from shared.config import settings
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


async def process_mesage(
        message: AbstractIncomingMessage,
        session_maker: async_sessionmaker[AsyncSession] = AsyncSessionMaker):
    async with message.process():
        body_dict = json_loads(message.body)
        print(body_dict)

        category_name = body_dict["category_name"]
        del body_dict["category_name"]

        async with ClientSession() as http_session, session_maker() as db_session:
            async with http_session.get(
                    "https://www.cbr-xml-daily.ru/daily_json.js"
            ) as resp:
                resp_dict = json_loads(await resp.text())
                usd_info_dict = resp_dict["Valute"]["USD"]
                dollar_price_in_rubles = usd_info_dict["Value"]
                ruble_price = body_dict["dollar_price"] * \
                    dollar_price_in_rubles

            query = select(Category).where(
                Category.category_name == category_name)

            category_id = (await db_session.execute(query)).scalars().one_or_none().uid

            package_obj = Package(
                **body_dict,
                ruble_price=ruble_price,
                category_id=category_id
            )

            db_session.add(package_obj)

            await db_session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
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
