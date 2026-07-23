from unittest.mock import AsyncMock, call, patch

import pytest

from src.core.consumer import base_handler
from src.domain.dataclasses import PackageRegistrationData
from src.domain.enums import CategoryEnum


def _registration_body() -> dict:
    return {
        "session_id": "consumer-session",
        "uid": "pkg-uid",
        "name": "Headphones",
        "weight": 0.25,
        "category_name": CategoryEnum.ELECTRONICS.value,
        "dollar_price": 10.0,
    }


async def test_base_handler_registers_package() -> None:
    repo = AsyncMock()

    with (
        patch("src.core.consumer.get_repo", return_value=repo),
        patch(
            "src.core.consumer.get_exchange_rate",
            AsyncMock(return_value=90.0),
        ),
    ):
        await base_handler(_registration_body())

    repo.register_package.assert_awaited_once()
    registered = repo.register_package.await_args.args[0]
    assert isinstance(registered, PackageRegistrationData)
    assert registered.exchange_rate == 90.0
    assert registered.name == "Headphones"
    assert registered.session_id == "consumer-session"
    assert registered.category_name == CategoryEnum.ELECTRONICS.value


async def test_base_handler_retries_before_success() -> None:
    repo = AsyncMock()
    repo.register_package = AsyncMock(
        side_effect=[RuntimeError("db down"), RuntimeError("db down"), None]
    )

    with (
        patch("src.core.consumer.get_repo", return_value=repo),
        patch(
            "src.core.consumer.get_exchange_rate",
            AsyncMock(return_value=90.0),
        ),
        patch("src.core.consumer.sleep", AsyncMock()) as sleep_mock,
    ):
        await base_handler(_registration_body())

    assert repo.register_package.await_count == 3
    sleep_mock.assert_has_awaits([call(2), call(4)])


async def test_base_handler_raises_after_max_retries() -> None:
    repo = AsyncMock()
    repo.register_package = AsyncMock(side_effect=RuntimeError("db down"))

    with (
        patch("src.core.consumer.get_repo", return_value=repo),
        patch(
            "src.core.consumer.get_exchange_rate",
            AsyncMock(return_value=90.0),
        ),
        patch("src.core.consumer.sleep", AsyncMock()) as sleep_mock,
        pytest.raises(RuntimeError, match="db down"),
    ):
        await base_handler(_registration_body())

    assert repo.register_package.await_count == 3
    sleep_mock.assert_has_awaits([call(2), call(4)])
