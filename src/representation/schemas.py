from typing import Annotated

from pydantic import BaseModel, Field, field_validator

from src.domain.enums import CategoryEnum


class PackageSchema(BaseModel):
    name: str
    weight: Annotated[float, Field(gt=0)]
    category_name: CategoryEnum
    dollar_price: Annotated[float, Field(ge=0)]

    @field_validator("category_name", mode="before")
    @classmethod
    def to_lowercase(cls, v: str) -> str:
        if isinstance(v, str):
            return v.lower()
        return v


class PackageResponse(BaseModel):
    uid: str
    name: str
    category: CategoryEnum
    weight: float
    dollar_price: float
    delivery_price: float


class CategoryResponse(BaseModel):
    uid: int
    category_name: CategoryEnum
