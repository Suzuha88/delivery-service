import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientResponseError
from tenacity import RetryError, wait_none

from src.infrastructure.http.cbr import CBR_RATES_URL, fetch_rub_exchange_rate


@pytest.fixture(autouse=True)
def disable_retry_backoff() -> None:
    fetch_rub_exchange_rate.retry.wait = wait_none()


def _make_response(*, status: int = 200, body: str | None = None) -> MagicMock:
    response = MagicMock()
    response.raise_for_status = MagicMock()
    if status >= 400:
        response.raise_for_status.side_effect = ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=status,
        )
    response.text = AsyncMock(
        return_value=body or json.dumps({"Valute": {"USD": {"Value": 91.5}}})
    )
    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=False)
    return response


def _patch_session(*responses: MagicMock) -> patch:
    session = MagicMock()
    session.get = MagicMock(side_effect=list(responses) if len(responses) > 1 else responses[0])
    if len(responses) == 1:
        session.get = MagicMock(return_value=responses[0])
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)
    return patch("src.infrastructure.http.cbr.ClientSession", return_value=session)


async def test_fetch_rub_exchange_rate_returns_usd_value() -> None:
    with _patch_session(_make_response()):
        rate = await fetch_rub_exchange_rate()

    assert rate == 91.5


async def test_fetch_rub_exchange_rate_retries_on_transient_failure() -> None:
    with _patch_session(
        _make_response(status=503),
        _make_response(status=503),
        _make_response(),
    ):
        rate = await fetch_rub_exchange_rate()

    assert rate == 91.5


async def test_fetch_rub_exchange_rate_raises_after_max_attempts() -> None:
    failing = _make_response(status=500)

    with (
        _patch_session(*[failing] * 10),
        pytest.raises(RetryError),
    ):
        await fetch_rub_exchange_rate()
