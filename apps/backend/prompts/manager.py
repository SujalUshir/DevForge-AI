"""
Prompt Management System.

Exposes PromptLoader, PromptValidator, and PromptCache to parse,
validate, and retrieve agent system prompts stored on the filesystem.
Prevents path traversal vulnerabilities using path resolution checks.
"""

import os
from pathlib import Path
from typing import Dict, Optional
import structlog

logger = structlog.get_logger(__name__)


class PromptSecurityError(Exception):
    """Raised when path traversal or unsafe file access is detected."""
    pass


class PromptNotFoundError(Exception):
    """Raised when a requested prompt markdown file does not exist."""
    pass


class PromptValidator:
    """
    Enforces path safety and checks prompt file specifications.
    """

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir.resolve()

    def validate_safe_path(self, relative_path: str) -> Path:
        """
        Validates that the resolved path lies within the base prompts directory.
        Prevents path traversal attacks (e.g., passing '../../etc/passwd').
        """
        target_path = Path(self.base_dir / relative_path).resolve()
        
        # Enforce target path is strictly within base directory
        if not str(target_path).startswith(str(self.base_dir)):
            logger.error("unsafe_prompt_path_detected", path=str(target_path), base=str(self.base_dir))
            raise PromptSecurityError(f"Access denied. Path traversal detected: '{relative_path}'")
            
        return target_path

    def prompt_exists(self, relative_path: str) -> bool:
        """
        Verify if the prompt exists on disk safely.
        """
        try:
            target = self.validate_safe_path(relative_path)
            return target.is_file()
        except PromptSecurityError:
            return False


class PromptCache:
    """
    In-memory caching mechanism for loaded prompts.
    """

    def __init__(self):
        self._cache: Dict[str, str] = {}

    def get(self, key: str) -> Optional[str]:
        return self._cache.get(key)

    def set(self, key: str, value: str) -> None:
        self._cache[key] = value

    def clear(self) -> None:
        self._cache.clear()


class PromptLoader:
    """
    Main API class to load, validate, and retrieve prompt templates.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        if not base_dir:
            # Default location: apps/backend/prompts/
            base_dir = Path(__file__).parent.resolve()
        
        self.validator = PromptValidator(base_dir)
        self.cache = PromptCache()

    def load_prompt(self, filename: str) -> str:
        """
        Loads prompt content from filesystem.
        Uses cached content if available.
        
        Args:
            filename: e.g. "product_lead.md" or "ceo.md"
        """
        # Ensure correct file extension
        if not filename.endswith(".md"):
            filename = f"{filename}.md"

        # Validate safety first to prevent traversal
        target_file = self.validator.validate_safe_path(filename)

        # Check cache first
        cached = self.cache.get(filename)
        if cached:
            logger.debug("prompt_cache_hit", filename=filename)
            return cached

        # Check existence
        if not target_file.is_file():
            logger.error("prompt_file_not_found", filename=filename)
            raise PromptNotFoundError(f"System prompt file '{filename}' could not be located.")

        # Read content from file
        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Cache it and return
        self.cache.set(filename, content)
        logger.info("prompt_loaded_and_cached", filename=filename)
        return content
