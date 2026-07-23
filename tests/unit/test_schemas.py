import pytest
from pydantic import ValidationError

from src.domain.enums import CategoryEnum
from src.representation.schemas import PackageSchema


def test_package_schema_accepts_valid_payload() -> None:
    package = PackageSchema(
        name="Laptop",
        weight=1.5,
        category_name="electronics",
        dollar_price=100.0,
    )
    assert package.name == "Laptop"
    assert package.weight == 1.5
    assert package.category_name is CategoryEnum.ELECTRONICS
    assert package.dollar_price == 100.0


def test_package_schema_lowercases_category() -> None:
    package = PackageSchema(
        name="Shirt",
        weight=0.2,
        category_name="CLOTHES",
        dollar_price=10.0,
    )
    assert package.category_name is CategoryEnum.CLOTHES


@pytest.mark.parametrize("weight", [0, -1.0])
def test_package_schema_rejects_non_positive_weight(weight: float) -> None:
    with pytest.raises(ValidationError):
        PackageSchema(
            name="Bad",
            weight=weight,
            category_name="misc",
            dollar_price=1.0,
        )


def test_package_schema_rejects_negative_price() -> None:
    with pytest.raises(ValidationError):
        PackageSchema(
            name="Bad",
            weight=1.0,
            category_name="miscellaneous",
            dollar_price=-0.01,
        )


def test_package_schema_rejects_unknown_category() -> None:
    with pytest.raises(ValidationError):
        PackageSchema(
            name="Bad",
            weight=1.0,
            category_name="food",
            dollar_price=1.0,
        )


def test_package_schema_allows_zero_price() -> None:
    package = PackageSchema(
        name="Free sample",
        weight=0.1,
        category_name="miscellaneous",
        dollar_price=0,
    )
    assert package.dollar_price == 0
