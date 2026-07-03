"""
LLM Adapter Layer.

Isolates model-specific logic from BaseAgent. Responsible for:
- Model invocation (async via google-genai)
- Token accounting & logging
- Retry logic with exponential backoff
- Structured JSON output validation (via Pydantic schema validation)
- Mock mode support for lockless testing and offline dry runs
"""

import os
import asyncio
from typing import Any, Dict, Type, Union, Optional
import structlog
from pydantic import BaseModel
from google import genai
from google.genai import types
from google.genai.errors import APIError

from config import settings

logger = structlog.get_logger(__name__)


class LLMAdapterError(Exception):
    """Base exception for LLM Adapter errors."""
    pass


class LLMAdapter:
    """
    Adapter layer connecting agents to Google's Gemini models.
    Supports structured output validation and automatic mock generation.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        self.mock_mode = not self.api_key or os.getenv("MOCK_LLM", "false").lower() == "true"
        
        # Initialize client if API key is present
        self.client = None
        if not self.mock_mode:
            try:
                self.client = genai.Client(api_key=self.api_key)
                logger.info("llm_adapter_initialized", mock_mode=False)
            except Exception as exc:
                logger.exception("llm_adapter_init_failed", error=str(exc))
                logger.warning("llm_adapter_falling_back_to_mock", reason="Client initialization failed")
                self.mock_mode = True
        else:
            logger.info("llm_adapter_initialized", mock_mode=True, reason="API key missing or MOCK_LLM=true")

    async def generate_structured_output(
        self,
        system_instruction: str,
        prompt: str,
        response_schema: Type[BaseModel],
        model: str = "gemini-2.5-flash",
        temperature: float = 0.2
    ) -> BaseModel:
        """
        Invokes LLM with strict JSON schema constraints and parses into Pydantic model.
        Falls back to generating structured mock content if mock_mode is active.
        """
        if self.mock_mode:
            logger.info("llm_adapter_mock_generation", model=model, schema=response_schema.__name__)
            # Sleep slightly to simulate model generation latency
            await asyncio.sleep(0.5)
            mock_data = self._generate_mock_data(response_schema)
            # Validate schema DDL format
            return response_schema.model_validate(mock_data)

        # Real Gemini API invocation using google-genai client
        attempt = 1
        max_attempts = settings.agent_max_retries
        backoff = 2.0

        while attempt <= max_attempts:
            try:
                logger.info(
                    "llm_adapter_api_call",
                    model=model,
                    attempt=attempt,
                    max_attempts=max_attempts
                )
                
                # Configuration specs with system instructions and JSON schemas
                config = types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=temperature,
                    response_mime_type="application/json",
                    response_schema=response_schema
                )

                # Invoke model asynchronously using client.aio
                response = await self.client.aio.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config
                )

                # Token accounting logging
                usage = getattr(response, "usage_metadata", None)
                if usage:
                    logger.info(
                        "llm_adapter_token_usage",
                        prompt_tokens=usage.prompt_token_count,
                        candidates_tokens=usage.candidates_token_count,
                        total_tokens=usage.total_token_count
                    )
                else:
                    logger.debug("llm_adapter_token_usage_unavailable")

                # Parse and validate structure
                result_text = response.text
                if not result_text:
                    raise LLMAdapterError("Model returned empty content response.")

                return response_schema.model_validate_json(result_text)

            except APIError as exc:
                logger.warning(
                    "llm_adapter_api_error",
                    attempt=attempt,
                    error=str(exc)
                )
                if attempt == max_attempts:
                    raise LLMAdapterError(f"Gemini API invocation failed after {max_attempts} attempts: {str(exc)}") from exc
                
                await asyncio.sleep(backoff * attempt)
                attempt += 1

            except Exception as exc:
                logger.exception("llm_adapter_unhandled_execution_error")
                raise LLMAdapterError(f"Structured LLM parsing execution failed: {str(exc)}") from exc

        raise LLMAdapterError("Execution pipeline exited unexpectedly.")

    def _generate_mock_data(self, model_class: Type[BaseModel]) -> Dict[str, Any]:
        """
        Recursively builds default mock dictionary complying with a Pydantic model's structure.
        """
        mock_data = {}
        for name, field in model_class.model_fields.items():
            field_type = field.annotation
            
            # Resolve Optional/Union fields
            if hasattr(field_type, "__origin__") and field_type.__origin__ is Union:
                args = field_type.__args__
                # Filter out NoneType (NoneType in python is type(None))
                field_type = next((t for t in args if t != type(None)), str)

            # Resolve lists
            if hasattr(field_type, "__origin__") and field_type.__origin__ is list:
                inner_type = field_type.__args__[0]
                if issubclass(inner_type, BaseModel):
                    mock_data[name] = [self._generate_mock_data(inner_type)]
                else:
                    mock_data[name] = [self._get_mock_primitive(inner_type)]
            # Resolve nested Pydantic models
            elif isinstance(field_type, type) and issubclass(field_type, BaseModel):
                mock_data[name] = self._generate_mock_data(field_type)
            # Resolve standard primitives
            elif isinstance(field_type, type):
                mock_data[name] = self._get_mock_primitive(field_type)
            else:
                mock_data[name] = "Mock String Output"
                
        return mock_data

    def _get_mock_primitive(self, t: Type) -> Any:
        if issubclass(t, str):
            return "Mock Generated structured output string placeholder"
        elif issubclass(t, int):
            return 100
        elif issubclass(t, float):
            return 99.9
        elif issubclass(t, bool):
            return True
        return None
