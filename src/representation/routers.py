import uuid
from json import dumps as json_dumps
from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Depends,
    Query,
    Request,
    status,
)
from fastapi.responses import JSONResponse

from src.domain.dataclasses import PackageFilters
from src.domain.message_queues import AbstractMessageQueuePublisher
from src.domain.repositories import AbstractRepository
from src.representation.schemas import (
    CategoryResponse,
    PackageResponse,
    PackageSchema,
    PackagesFilter,
)
from src.representation.utils import get_session_id

get_router = APIRouter()
post_router = APIRouter()


def get_repository() -> AbstractRepository:
    return AbstractRepository()


@post_router.post("/register")
async def register(
    package: PackageSchema,
    request: Request,
) -> JSONResponse:
    """Send package info for registration into message queue"""

    dict_body = package.model_dump(mode="json")
    mq: AbstractMessageQueuePublisher = request.app.state.mq

    uid = str(uuid.uuid4())
    session_id = get_session_id(request)

    dict_body["uid"] = uid
    dict_body["session_id"] = session_id

    byte_body = json_dumps(dict_body).encode("utf-8")

    await mq.send_registration_message(byte_body)

    return JSONResponse(
        content={"message": f"Package with {uid=} sent for registration"},
        status_code=status.HTTP_202_ACCEPTED,
    )


@get_router.get("/packages/{package_id}", response_model=PackageResponse)
async def get_package(
    request: Request,
    package_id: str,
    repository: Annotated[AbstractRepository, Depends(get_repository)],
) -> dict[str, Any]:
    """
    Get package of same user by id
    Even if id exists will not return package of other user
    """
    session_id = get_session_id(request)
    res = await repository.get_package(package_id, session_id)
    return res


@get_router.get("/packages", response_model=list[PackageResponse])
async def get_all_packages(
    request: Request,
    repository: Annotated[AbstractRepository, Depends(get_repository)],
    options: Annotated[PackagesFilter, Query()],
) -> list[dict[str, Any]]:
    """Get all packages"""
    session_id = get_session_id(request)
    filters = PackageFilters(**options.model_dump())
    return await repository.get_all_packages(session_id, filters)


@get_router.get("/categories", response_model=list[CategoryResponse])
async def get_all_categories(
    repository: Annotated[AbstractRepository, Depends(get_repository)],
) -> list[dict[str, Any]]:
    """Get all categories"""
    return await repository.get_all_categories()
