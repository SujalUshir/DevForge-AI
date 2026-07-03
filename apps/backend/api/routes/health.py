"""
Health check endpoint.

Exposes GET /api/health — used by:
  - Container orchestrators (Docker healthcheck)
  - Frontend startup probe (verifies backend is ready)
  - Monitoring systems (Render, Railway, uptime monitors)
"""

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: datetime


@router.get(
    "",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns service status and metadata. Used by orchestrators and monitors.",
)
async def health_check() -> HealthResponse:
    from config import settings

    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
        timestamp=datetime.now(tz=timezone.utc),
    )
