import json

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.enums import CategoryEnum
from src.infrastructure.sql.models import Category, Package
from tests.conftest import InMemoryMessageQueue


async def test_get_categories(api_client: AsyncClient) -> None:
    response = await api_client.get("/categories")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == len(CategoryEnum)
    names = {item["category_name"] for item in body}
    assert names == {c.value for c in CategoryEnum}


async def test_get_packages_empty_returns_404(api_client: AsyncClient) -> None:
    api_client.cookies.set("session_id", "session-a")
    response = await api_client.get("/packages")
    assert response.status_code == 404
    assert response.json()["error"] == "Package not found"


async def test_get_packages_and_get_by_id(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    category = (
        (
            await db_session.execute(
                select(Category).where(
                    Category.category_name == CategoryEnum.ELECTRONICS
                )
            )
        )
        .scalars()
        .one()
    )

    package = Package(
        uid="phone-uid",
        session_id="session-a",
        user_seq=0,
        name="Phone",
        weight=0.3,
        category_id=category.uid,
        dollar_price=200.0,
        delivery_price=18000.0,
    )
    db_session.add(package)
    await db_session.commit()

    api_client.cookies.set("session_id", "session-a")

    list_response = await api_client.get("/packages")
    assert list_response.status_code == 200
    packages = list_response.json()
    assert len(packages) == 1
    assert packages[0]["name"] == "Phone"
    assert packages[0]["category"] == "electronics"

    detail = await api_client.get("/packages/phone-uid")
    assert detail.status_code == 200
    assert detail.json()["uid"] == "phone-uid"
    assert detail.json()["dollar_price"] == 200.0


async def test_get_package_not_found(api_client: AsyncClient) -> None:
    api_client.cookies.set("session_id", "session-a")
    response = await api_client.get("/packages/missing-uid")
    assert response.status_code == 404
    assert response.json()["error"] == "Package not found"


async def test_get_package_wrong_session_returns_404(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    category = (
        (
            await db_session.execute(
                select(Category).where(Category.category_name == CategoryEnum.CLOTHES)
            )
        )
        .scalars()
        .one()
    )

    package = Package(
        uid="jacket-uid",
        session_id="owner-session",
        user_seq=0,
        name="Jacket",
        weight=1.0,
        category_id=category.uid,
        dollar_price=50.0,
        delivery_price=4500.0,
    )
    db_session.add(package)
    await db_session.commit()

    api_client.cookies.set("session_id", "other-session")
    response = await api_client.get("/packages/jacket-uid")
    assert response.status_code == 404


async def test_register_publishes_message_with_session_id(
    api_client: AsyncClient,
    mock_mq: InMemoryMessageQueue,
) -> None:
    api_client.cookies.set("session_id", "session-reg")

    payload = {
        "name": "Tablet",
        "weight": 0.5,
        "category_name": "electronics",
        "dollar_price": 120.0,
    }
    response = await api_client.post("/register", json=payload)

    assert response.status_code == 202
    assert "sent for registration" in response.json()["message"]
    assert len(mock_mq.sent_messages) == 1

    body = json.loads(mock_mq.sent_messages[0].decode("utf-8"))
    assert body["name"] == "Tablet"
    assert body["session_id"] == "session-reg"
    assert body["category_name"] == "electronics"
    assert "uid" in body


async def test_register_publish_failure_returns_500(
    api_client: AsyncClient,
    mock_mq: InMemoryMessageQueue,
) -> None:
    api_client.cookies.set("session_id", "session-reg")
    mock_mq.publish_error = RuntimeError("broker down")

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
    assert "broker down" in response.json()["details"]


async def test_validation_error_returns_consistent_shape(
    api_client: AsyncClient,
) -> None:
    api_client.cookies.set("session_id", "session-reg")
    response = await api_client.post(
        "/register",
        json={
            "name": "Bad",
            "weight": -1,
            "category_name": "electronics",
            "dollar_price": 10.0,
        },
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "Validation failed"
    assert "details" in body


async def test_new_visitor_gets_session_cookie(api_client: AsyncClient) -> None:
    response = await api_client.get("/packages")
    assert response.status_code == 404
    set_cookie = response.headers.get("set-cookie", "")
    assert "session_id=" in set_cookie
