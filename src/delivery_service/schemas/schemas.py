from typing import Annotated

from pydantic import BaseModel, Field

from models.models import PackageType


class PackageSchema(BaseModel):
    name: str
    weight: Annotated[float, Field(gt=0)]
    category: PackageType
    j
