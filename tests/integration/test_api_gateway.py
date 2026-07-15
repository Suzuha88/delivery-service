import json
from unittest.mock import AsyncMock

from httpx2 import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.enums import CategoryEnum
from shared.db.models import Category, Package


async def test_get_categories(api_client: AsyncClient) -> None:
    response = await api_client.get("/categories")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == len(CategoryEnum)
    names = {item["category_name"] for item in body}
    assert names == {c.value for c in CategoryEnum}


async def test_get_packages_empty(api_client: AsyncClient) -> None:
    api_client.cookies.set("session_id", "session-a")
    response = await api_client.get("/packages")
    assert response.status_code == 200
    assert response.json() == []


async def test_get_packages_and_get_by_id(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    category = (
        await db_session.execute(
            select(Category).where(Category.category_name == CategoryEnum.ELECTRONICS)
        )
    ).scalars().one()

    package = Package(
        session_id="session-a",
        name="Phone",
        weight=0.3,
        category_id=category.uid,
        dollar_price=200.0,
        ruble_price=18000.0,
    )
    db_session.add(package)
    await db_session.commit()
    await db_session.refresh(package)

    api_client.cookies.set("session_id", "session-a")

    list_response = await api_client.get("/packages")
    assert list_response.status_code == 200
    packages = list_response.json()
    assert len(packages) == 1
    assert packages[0]["name"] == "Phone"
    assert packages[0]["category"] == "electronics"

    detail = await api_client.get(f"/packages/{package.uid}")
    assert detail.status_code == 200
    assert detail.json()["uid"] == package.uid
    assert detail.json()["dollar_price"] == 200.0


async def test_get_package_not_found(api_client: AsyncClient) -> None:
    api_client.cookies.set("session_id", "session-a")
    response = await api_client.get("/packages/99999")
    assert response.status_code == 404
    assert response.json()["message"] == "No packages with this id"


async def test_get_package_wrong_session_returns_404(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    category = (
        await db_session.execute(
            select(Category).where(Category.category_name == CategoryEnum.CLOTHES)
        )
    ).scalars().one()

    package = Package(
        session_id="owner-session",
        name="Jacket",
        weight=1.0,
        category_id=category.uid,
        dollar_price=50.0,
        ruble_price=4500.0,
    )
    db_session.add(package)
    await db_session.commit()
    await db_session.refresh(package)

    api_client.cookies.set("session_id", "other-session")
    response = await api_client.get(f"/packages/{package.uid}")
    assert response.status_code == 404


async def test_register_publishes_message_with_session_id(
    api_client: AsyncClient,
    mock_rabbit_channel,
) -> None:
    api_client.cookies.set("session_id", "session-reg")

    payload = {
        "name": "Tablet",
        "weight": 0.5,
        "category_name": "electronics",
        "dollar_price": 120.0,
    }
    response = await api_client.post("/register", json=payload)

    assert response.status_code == 200
    assert response.json()["message"] == "Package sent for registration"
    mock_rabbit_channel.default_exchange.publish.assert_awaited_once()

    published = mock_rabbit_channel.default_exchange.publish.await_args
    message = published.args[0]
    body = json.loads(message.body.decode("utf-8"))
    assert body["name"] == "Tablet"
    assert body["session_id"] == "session-reg"
    assert body["category_name"] == "electronics"
    assert published.kwargs["routing_key"] == "hello"


async def test_register_publish_failure_returns_500(
    api_client: AsyncClient,
    mock_rabbit_channel,
) -> None:
    api_client.cookies.set("session_id", "session-reg")
    mock_rabbit_channel.default_exchange.publish = AsyncMock(
        side_effect=RuntimeError("broker down")
    )

    response = await api_client.post(
        "/register",
        json={
            "name": "Tablet",
            "weight": 0.5,
            "category_name": "electronics",
            "dollar_price": 120.0,
        },
    )

    assert response.status_code == 500
    assert "Couldn't send package for registration" in response.json()["error"]


async def test_new_visitor_gets_session_cookie(api_client: AsyncClient) -> None:
    response = await api_client.get("/packages")
    assert response.status_code == 200
    # Secure cookies may not be stored by httpx on http://; Set-Cookie header must exist
    set_cookie = response.headers.get("set-cookie", "")
    assert "session_id=" in set_cookie
