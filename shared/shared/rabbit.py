from json import loads as json_loads

from aio_pika import connect
from aio_pika.abc import (
    AbstractChannel,
    AbstractConnection,
    AbstractIncomingMessage,
    AbstractQueue,
)
from aiohttp import ClientSession
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .config import settings
from .db import AsyncSessionMaker
from .models import Category, Package
from .rd_cache import get_rates


async def initialize_rabbitmq(
) -> tuple[AbstractConnection, AbstractChannel, AbstractQueue]:
    connection = await connect(settings.RABBIT_URL)
    channel = await connection.channel()
    queue = await channel.declare_queue("hello", durable=True)

    return (connection, channel, queue)


async def process_registration_message(
        message: AbstractIncomingMessage,
        session_maker: async_sessionmaker[AsyncSession] = AsyncSessionMaker) -> None:
    async with message.process():
        body_dict = json_loads(message.body)
        print(body_dict)

        category_name = body_dict["category_name"]
        del body_dict["category_name"]

        async with session_maker() as db_session:
            resp_dict = json_loads(await get_rates())
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
