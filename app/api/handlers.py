"""Global exception handlers."""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    AlreadyExistsError,
    InsufficientStockError,
    InvalidMovementError,
    LogiTrackError,
)

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AlreadyExistsError)
    async def already_exists_handler(
        request: Request, exc: AlreadyExistsError
    ) -> JSONResponse:
        logger.warning("AlreadyExistsError: %s", exc.detail)
        return JSONResponse(
            status_code=409,
            content={"detail": exc.detail},
        )

    @app.exception_handler(InsufficientStockError)
    async def insufficient_stock_handler(
        request: Request, exc: InsufficientStockError
    ) -> JSONResponse:
        logger.warning("InsufficientStockError: %s", exc.detail)
        return JSONResponse(
            status_code=400,
            content={
                "detail": exc.detail,
                "product_id": exc.product_id,
                "warehouse_id": exc.warehouse_id,
                "requested": exc.requested,
                "available": exc.available,
            },
        )

    @app.exception_handler(InvalidMovementError)
    async def invalid_movement_handler(
        request: Request, exc: InvalidMovementError
    ) -> JSONResponse:
        logger.warning("InvalidMovementError: %s", exc.detail)
        return JSONResponse(
            status_code=400,
            content={"detail": exc.detail},
        )

    @app.exception_handler(LogiTrackError)
    async def logitrack_error_handler(
        request: Request, exc: LogiTrackError
    ) -> JSONResponse:
        """Catch-all for any LogiTrackError subclass."""
        logger.error("Unhandled LogiTrackError: %s", exc.detail)
        return JSONResponse(
            status_code=500,
            content={"detail": exc.detail},
        )
