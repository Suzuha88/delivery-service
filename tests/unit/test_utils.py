from starlette.requests import Request
from utils.utils import get_session_id


def _make_request(
    *,
    cookies: dict[str, str] | None = None,
    session_id_state: str | None = None,
) -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 123),
        "server": ("test", 80),
    }
    request = Request(scope)
    if cookies:
        request._cookies = cookies
    if session_id_state is not None:
        request.state.session_id = session_id_state
    return request


def test_get_session_id_from_cookie() -> None:
    request = _make_request(cookies={"session_id": "cookie-id"})
    assert get_session_id(request) == "cookie-id"


def test_get_session_id_from_state_when_cookie_missing() -> None:
    request = _make_request(session_id_state="state-id")
    assert get_session_id(request) == "state-id"


def test_get_session_id_prefers_cookie_over_state() -> None:
    request = _make_request(
        cookies={"session_id": "cookie-id"},
        session_id_state="state-id",
    )
    assert get_session_id(request) == "cookie-id"
