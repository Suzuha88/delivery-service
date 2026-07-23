from dataclasses import dataclass

from src.domain.enums import CategoryEnum


@dataclass
class PackageRegistrationData:
    uid: str
    session_id: str
    name: str
    weight: float
    dollar_price: float

    category_name: CategoryEnum
    exchange_rate: float


@dataclass
class PackageFilters:
    start: int
    limit: int
    category: CategoryEnum | None
    delivery_price_has_been_calculated: bool | None
