from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse

from src.core.logging import logger
from src.domain.exceptions import PackageIsPendingError, PackageNotFoundError


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        # request: Request,
        exc: HTTPException,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail},
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        logger.warning(
            f"Validation error on {request.method} {request.url.path}: {exc.errors()}"
        )
        return JSONResponse(
            status_code=422,
            content={"error": "Validation failed", "details": exc.errors()},
        )

    @app.exception_handler(PackageIsPendingError)
    @app.exception_handler(PackageNotFoundError)
    async def package_exception_handler(
        request: Request, exc: PackageIsPendingError | PackageNotFoundError
    ) -> JSONResponse:
        logger.exception("Couldn't query a package")
        return JSONResponse(
            status_code=404,
            content={"error": "Package not found", "details": exc.description},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception(f"Unhandled error on {request.method} {request.url.path}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"},
        )
