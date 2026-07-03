"""
Central API router.

All route modules are registered here with their prefix and tags.
This file is the single import point for main.py — adding a new
feature only requires registering its router here.
"""

from fastapi import APIRouter

from api.routes import health, projects

api_router = APIRouter()

# ── Core routes ───────────────────────────────────────────────────────────────
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])

