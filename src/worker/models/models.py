
from sqlalchemy import CheckConstraint, Enum, ForeignKey, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from shared import CategoryEnum


class Base(DeclarativeBase):
    pass


class Category(Base):
    __tablename__ = "categories"

    uid: Mapped[int] = mapped_column(primary_key=True)
    category_name: Mapped[CategoryEnum] = mapped_column(Enum(CategoryEnum))

    @classmethod
    async def ensure_populated(cls, session: AsyncSession) -> None:
        """Ensure all categories exist in the table"""

        res = await session.execute(select(cls))

        existing = {row.category_name for row in res.scalars().all()}

        for ctg in CategoryEnum:
            if ctg not in existing:
                session.add(cls(
                    category_name=ctg
                ))

        await session.commit()


class Package(Base):
    __tablename__ = "packages"

    uid: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(index=True)
    name: Mapped[str]
    weight: Mapped[float] = mapped_column(
        CheckConstraint("weight > 0", name="ck_weight_positive"))
    category_id: Mapped[int] = mapped_column(ForeignKey(Category.uid))
    category: Mapped["Category"] = relationship()
    dollar_price: Mapped[float] = mapped_column(CheckConstraint(
        "dollar_price >= 0", name="ck_price_not_negative"))
    ruble_price: Mapped[float | None]
