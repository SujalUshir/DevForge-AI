"""
LLM Adapter Layer.

Isolates model-specific logic from BaseAgent. Responsible for:
- Model invocation (async via Google ADK)
- Token accounting & logging
- Retry logic with exponential backoff
- Structured JSON output validation (via Pydantic schema validation)
- Mock mode support for lockless testing and offline dry runs
"""

import os
import asyncio
from uuid import uuid4
from typing import Any, Dict, Type, Union, Optional
import structlog
from pydantic import BaseModel
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.genai.errors import APIError

from config import settings

logger = structlog.get_logger(__name__)


class LLMAdapterError(Exception):
    """Base exception for LLM Adapter errors."""
    pass


class ADKAdapter:
    """
    Internal adapter for executing one-shot structured Gemini calls through Google ADK.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.app_name = "devforge-ai"
        self.user_id = "devforge-backend"
        self.session_service = InMemorySessionService()

        # ADK's Gemini model integration reads Google's standard env var.
        # Preserve the existing DevForge GEMINI_API_KEY contract by bridging it here.
        if self.api_key:
            os.environ["GOOGLE_API_KEY"] = self.api_key

    async def generate_structured_output(
        self,
        system_instruction: str,
        prompt: str,
        response_schema: Type[BaseModel],
        model: str,
        temperature: float
    ) -> BaseModel:
        output_key = "structured_response"
        agent = LlmAgent(
            name="devforge_structured_agent",
            model=model,
            instruction=system_instruction,
            output_schema=response_schema,
            output_key=output_key,
            generate_content_config=types.GenerateContentConfig(
                temperature=temperature
            ),
        )
        runner = Runner(
            app_name=self.app_name,
            agent=agent,
            session_service=self.session_service,
        )
        session_id = f"llm-{uuid4().hex}"
        await self.session_service.create_session(
            app_name=self.app_name,
            user_id=self.user_id,
            session_id=session_id,
        )

        final_text = ""
        structured_payload: Optional[Any] = None
        try:
            async for event in runner.run_async(
                user_id=self.user_id,
                session_id=session_id,
                new_message=types.UserContent(parts=[types.Part(text=prompt)]),
            ):
                state_delta = getattr(
                    getattr(event, "actions", None),
                    "state_delta",
                    None,
                )
                if state_delta and output_key in state_delta:
                    structured_payload = state_delta[output_key]

                if event.is_final_response():
                    event_text = self._extract_event_text(event)
                    if event_text:
                        final_text = event_text
        finally:
            await runner.close()

        if structured_payload is not None:
            return response_schema.model_validate(structured_payload)
        if final_text:
            return response_schema.model_validate_json(final_text)
        raise LLMAdapterError("ADK returned no structured content response.")

    def _extract_event_text(self, event: Any) -> str:
        content = getattr(event, "content", None)
        parts = getattr(content, "parts", None) or []
        return "".join(
            part.text
            for part in parts
            if getattr(part, "text", None) and not getattr(part, "thought", False)
        )


class LLMAdapter:
    """
    Adapter layer connecting agents to Google's Gemini models.
    Supports structured output validation and automatic mock generation.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (
            settings.gemini_api_key or os.getenv("GEMINI_API_KEY", "")
            if api_key is None
            else api_key
        )
        self.mock_mode = not self.api_key or os.getenv("MOCK_LLM", "false").lower() == "true"
        
        # Initialize ADK adapter if API key is present
        self.adk_adapter = None
        if not self.mock_mode:
            try:
                self.adk_adapter = ADKAdapter(api_key=self.api_key)
                logger.info("llm_adapter_initialized", mock_mode=False, provider="google_adk")
            except Exception as exc:
                logger.exception("llm_adapter_init_failed", error=str(exc))
                logger.warning("llm_adapter_falling_back_to_mock", reason="ADK initialization failed")
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

        # Real Gemini API invocation through Google ADK
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

                if not self.adk_adapter:
                    raise LLMAdapterError("ADK adapter was not initialized.")

                response = await self.adk_adapter.generate_structured_output(
                    system_instruction=system_instruction,
                    prompt=prompt,
                    response_schema=response_schema,
                    model=model,
                    temperature=temperature
                )
                logger.debug("llm_adapter_token_usage_unavailable", provider="google_adk")
                return response

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
