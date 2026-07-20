from sqlalchemy import BigInteger, CheckConstraint, Enum, ForeignKey, event, text
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
    user_seq: Mapped[int] = mapped_column(BigInteger, index=True)

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


class UserSequence(Base):
    __tablename__ = "user_sequences"

    session_id: Mapped[str] = mapped_column(primary_key=True)
    user_seq: Mapped[int] = mapped_column(BigInteger, default=0)


@event.listens_for(Package, "before_insert")
def set_user_seq(mapper, connection, target):
    """Automatically set user sequence in packages table"""

    result = connection.execute(
        text("""
        INSERT INTO user_sequences (session_id, user_seq)
        VALUES (:session_id, 0)
        ON CONFLICT (session_id)
        DO UPDATE SET user_seq = user_sequences.user_seq + 1
        RETURNING user_seq
        """),
        {"session_id": target.session_id},
    )
    target.user_seq = result.scalar()
