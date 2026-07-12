from typing import Annotated

from pydantic import BaseModel, Field, field_validator

from core.enums import CategoryEnum


class PackageSchema(BaseModel):
    name: str
    weight: Annotated[float, Field(gt=0)]
    category: CategoryEnum
    dollar_price: Annotated[float, Field(ge=0)]

    @field_validator("category", mode="before")
    @classmethod
    def to_lowercase(cls, v: str) -> str:
        if isinstance(v, str):
            return v.lower()
        return v
