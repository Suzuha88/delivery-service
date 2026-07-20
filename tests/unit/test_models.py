from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.enums import CategoryEnum
from shared.db.models import Category


async def test_ensure_populated_inserts_all_categories(
    db_session: AsyncSession,
) -> None:
    result = await db_session.execute(select(Category))
    names = {row.category_name for row in result.scalars().all()}
    assert names == set(CategoryEnum)


async def test_ensure_populated_is_idempotent(
    db_session: AsyncSession,
    session_maker,
) -> None:
    await Category.ensure_populated(db_session)

    async with session_maker() as session:
        await Category.ensure_populated(session)
        result = await session.execute(select(Category))
        assert len(result.scalars().all()) == len(CategoryEnum)
