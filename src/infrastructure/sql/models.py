
from sqlalchemy import CheckConstraint, Enum, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from src.domain.enums import CategoryEnum


class Base(DeclarativeBase):
    pass


class Category(Base):
    __tablename__ = "categories"

    uid: Mapped[int] = mapped_column(primary_key=True)
    category_name: Mapped[CategoryEnum] = mapped_column(Enum(CategoryEnum))


class Package(Base):
    __tablename__ = "packages"

    uid: Mapped[str] = mapped_column(primary_key=True, autoincrement=False)
    session_id: Mapped[str] = mapped_column(index=True)
    name: Mapped[str]
    weight: Mapped[float] = mapped_column(
        CheckConstraint("weight > 0", name="ck_weight_positive")
    )
    category_id: Mapped[int] = mapped_column(ForeignKey(Category.uid))
    category: Mapped["Category"] = relationship()
    dollar_price: Mapped[float] = mapped_column(
        CheckConstraint("dollar_price >= 0", name="ck_price_not_negative")
    )
    delivery_price: Mapped[float | None]
