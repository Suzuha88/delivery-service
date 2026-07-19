from secrets import token_hex

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import RequestResponseEndpoint

from src.logging import logger


def register_middleware(app: FastAPI) -> None:

    @app.middleware("http")
    async def add_session_id(
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """
        Check if request has session id, if not
        Forward it with state variable of same name, get response and set session id
        """
        session_id = request.cookies.get("session_id")

        if not session_id:
            session_id = request.state.session_id = token_hex(16)
            response = await call_next(request)
            response.set_cookie(
                key="session_id",
                value=session_id,
                httponly=True,
                secure=True,
            )
            return response

        return await call_next(request)


def register_request_logging(app: FastAPI) -> None:
    @app.middleware("http")
    async def log_requests(
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        response = await call_next(request)
        logger.info(
            f"{request.method} {request.url.path} -> {response.status_code=}")
        return response
