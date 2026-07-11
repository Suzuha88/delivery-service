from sqlalchemy import Column, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Test(Base):
    __tablename__ = "test"

    text = Column(String, primary_key=True)
