from json import loads as json_loads

from aio_pika import connect
from aio_pika.abc import (
    AbstractChannel,
    AbstractConnection,
    AbstractIncomingMessage,
    AbstractQueue,
)
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..config import settings
from ..db.db import AsyncSessionMaker
from ..db.models import Category, Package
from ..rd_cache import get_rates


async def initialize_rabbitmq(
) -> tuple[AbstractConnection, AbstractChannel, AbstractQueue]:
    """
    Create connection to RabbitMQ.

    Returns rabbitmq connection, channel, queue instances as a tuple.
    """
    connection = await connect(settings.RABBIT_URL)
    channel = await connection.channel()
    queue = await channel.declare_queue("hello", durable=True)
    logger.info(f"Connected to RabbitMQ queue={queue.name}")
    return connection, channel, queue


async def process_registration_message(
        message: AbstractIncomingMessage,
        session_maker: async_sessionmaker[AsyncSession] = AsyncSessionMaker,
) -> None:
    """
    Process a registration message:
    fetch FX rates, calculate ruble price, and insert the package.
    """
    async with message.process():
        try:
            body_dict = json_loads(message.body)
            logger.info(
                f"Processing package registration session_id={
                    body_dict.get("session_id")} name={body_dict.get("name")}"
            )

            category_name = body_dict.pop("category_name")

            async with session_maker() as db_session:
                resp_dict = json_loads(await get_rates())
                dollar_price_in_rubles = resp_dict["Valute"]["USD"]["Value"]
                ruble_price = body_dict["dollar_price"] * \
                    dollar_price_in_rubles

                category = (
                    await db_session.execute(
                        select(Category).where(
                            Category.category_name == category_name
                        )
                    )
                ).scalars().one_or_none()

                if category is None:
                    raise ValueError(f"Unknown category: {category_name}")

                package_obj = Package(
                    **body_dict,
                    ruble_price=ruble_price,
                    category_id=category.uid,
                )
                db_session.add(package_obj)
                await db_session.commit()
                logger.info(
                    f"Registered package session_id={body_dict.get("session_id")} category={category_name} ruble_price={ruble_price}"
                )
        except Exception:
            logger.exception("Failed to process registration message")
            raise
