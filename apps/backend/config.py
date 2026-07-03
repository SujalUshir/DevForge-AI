"""
Application configuration — sourced from environment variables or .env file.

All fields include sensible defaults for zero-config local development.
The Settings class uses Pydantic v2 BaseSettings for automatic .env parsing,
type coercion, and validation.
"""

from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        # Allow extra fields to be ignored (forward compatibility)
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────
    app_name: str = "DevForge AI"
    app_version: str = "1.0.0"
    debug: bool = False

    # ── Server ────────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000

    # ── Logging ───────────────────────────────────────────────────
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")

    # ── CORS ──────────────────────────────────────────────────────
    # The Next.js dev server on port 3000 is always allowed.
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://[::1]:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            origins = [o.strip() for o in v.split(",") if o.strip()]
        elif isinstance(v, list):
            origins = v
        else:
            origins = []
        
        defaults = ["http://localhost:3000", "http://127.0.0.1:3000", "http://[::1]:3000"]
        for d in defaults:
            if d not in origins:
                origins.append(d)
        return origins

    # ── Storage ───────────────────────────────────────────────────
    # The workspace directory where generated project blueprints are written.
    # Relative to apps/backend/ during local development.
    output_dir: Path = Path("./workspace")

    # ── Google AI ─────────────────────────────────────────────────
    # Required from Milestone 4 onward.
    gemini_api_key: str = ""

    # ── Agent execution limits ────────────────────────────────────
    # Maximum revision loops the Engineering Director may request before failing.
    max_revision_attempts: int = Field(default=2, ge=1, le=5)

    # Seconds before a single agent LLM call is considered timed out.
    agent_timeout_seconds: int = Field(default=120, ge=10, le=600)

    # Gemini API retry count per agent before the phase is marked FAILED.
    agent_max_retries: int = Field(default=3, ge=1, le=10)

    def ensure_output_dir(self) -> None:
        """Create the output directory if it does not exist."""
        self.output_dir.mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    """
    FastAPI dependency injection factory.

    Usage::

        @router.get("/example")
        async def handler(settings: Annotated[Settings, Depends(get_settings)]):
            ...
    """
    return Settings()


# Module-level singleton used outside dependency injection context.
# Import this from other modules instead of instantiating Settings directly.
settings = Settings()
