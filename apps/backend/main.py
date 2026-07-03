"""
DevForge AI — FastAPI application entry point.

Uses the application factory pattern so the app instance can be
imported in tests without side effects (no startup events fire
until a test client or server is explicitly created).

Run locally::

    uv run uvicorn main:app --reload --port 8000
"""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.middleware import RequestLoggingMiddleware
from api.router import api_router
from config import settings
from logging_config import configure_logging

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Startup: configure logging, ensure required directories exist, log
             service info for visibility in container logs.
    Shutdown: emit shutdown log (useful for distinguishing clean vs crash).
    """
    configure_logging(settings.log_level)
    settings.ensure_output_dir()

    logger.info(
        "devforge_starting",
        service=settings.app_name,
        version=settings.app_version,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        output_dir=str(settings.output_dir),
    )

    yield

    logger.info("devforge_shutdown", service=settings.app_name)


def create_application() -> FastAPI:
    """
    Application factory.

    Returns a fully configured FastAPI instance with:
    - CORS middleware (configured from settings)
    - Request logging middleware
    - All API routes registered under /api
    """
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Autonomous AI software company that transforms ideas into "
            "production-ready engineering blueprints via multi-agent collaboration."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ── Middleware (applied in reverse order — last registered runs first) ────
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routes ────────────────────────────────────────────────────────────────
    app.include_router(api_router, prefix="/api")

    return app


# The application instance consumed by uvicorn.
app = create_application()
