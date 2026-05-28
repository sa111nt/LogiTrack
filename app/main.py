import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.handlers import register_exception_handlers
from app.config import settings
from app.routers import auth as auth_router
from app.routers import category as category_router
from app.routers import product as product_router
from app.routers import stock as stock_router
from app.routers import supplier as supplier_router
from app.routers import user as user_router
from app.routers import warehouse as warehouse_router

# Setup logging configuration
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# FastAPI Lifespan Manager
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup phase
    logger.info("LogiTrack API starting up - version %s", settings.app_version)
    yield
    # Shutdown phase
    logger.info("LogiTrack API shutting down")


# Initialize FastAPI Application
app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description=(
        "LogiTrack - ERP System for Inventory and Logistics Management.\n\n"
        "REST API built on FastAPI and PostgreSQL."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register global exception handlers
register_exception_handlers(app)


# Health-check Endpoint
@app.get(
    "/health",
    tags=["System"],
    summary="Health check",
    response_description="Server health status and version metadata",
)
async def health_check() -> dict[str, str]:
    logger.debug("Health check endpoint called")
    return {
        "status": "ok",
        "service": settings.app_title,
        "version": settings.app_version,
    }


API_V1_PREFIX = "/api/v1"

app.include_router(auth_router.router, prefix=API_V1_PREFIX)
app.include_router(user_router.router, prefix=API_V1_PREFIX)
app.include_router(category_router.router, prefix=API_V1_PREFIX)
app.include_router(supplier_router.router, prefix=API_V1_PREFIX)
app.include_router(product_router.router, prefix=API_V1_PREFIX)
app.include_router(warehouse_router.router, prefix=API_V1_PREFIX)
app.include_router(stock_router.router, prefix=API_V1_PREFIX)
