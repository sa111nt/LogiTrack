import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

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
        "LogiTrack — ERP System for Inventory and Logistics Management.\n\n"
        "Production-Ready REST API built on FastAPI and PostgreSQL."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production via environment variables
    allow_credentials=True,
    allow_methods=["*"],  # Allows GET, POST, PUT, DELETE, OPTIONS, etc.
    allow_headers=["*"],
)


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
