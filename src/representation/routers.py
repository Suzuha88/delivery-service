import uuid
from json import dumps as json_dumps
from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Depends,
    Request,
)

from src.domain.message_queues import AbstractMessageQueue
from src.domain.repositories import AbstractRepository
from src.representation.schemas import CategoryResponse, PackageResponse, PackageSchema
from src.representation.utils import get_session_id

get_router = APIRouter()
post_router = APIRouter()


def get_repository() -> AbstractRepository:
    return AbstractRepository()


@post_router.post("/register")
async def register(
    package: PackageSchema,
    request: Request,
) -> dict[str, str]:
    """Send package info for registration into message queue"""

    dict_body = package.model_dump(mode="json")
    mq: AbstractMessageQueue = request.app.state.mq

    uid = str(uuid.uuid4())
    session_id = get_session_id(request)

    dict_body["uid"] = uid
    dict_body["session_id"] = session_id

    byte_body = json_dumps(dict_body).encode("utf-8")

    await mq.send_registration_message(byte_body)

    return {"message": f"Package with {uid=} sent for registration"}


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
    request: Request, repository: Annotated[AbstractRepository, Depends(get_repository)]
) -> list[dict[str, Any]]:
    """Get all packages"""
    session_id = get_session_id(request)
    try:
        return await repository.get_all_packages(session_id)
    except Exception as e:
        raise e


@get_router.get("/categories", response_model=list[CategoryResponse])
async def get_all_categories(
    repository: Annotated[AbstractRepository, Depends(get_repository)],
) -> list[dict[str, Any]]:
    """Get all categories"""
    return await repository.get_all_categories()
