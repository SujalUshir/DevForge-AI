"""
BaseAgent abstract class defining lifecycle and context hooks.
"""

from abc import ABC, abstractmethod
import asyncio
from datetime import datetime
import structlog
from typing import Any, Dict, Optional

from context.manager import ContextManager
from agents.models import AgentStatus, AgentResponse
from agents.exceptions import AgentInitializationError, AgentExecutionError, AgentValidationError
from agents.llm_adapter import LLMAdapter

logger = structlog.get_logger(__name__)


class BaseAgent(ABC):
    """
    Abstract Base Class for all AI agents.
    
    Subclasses must implement:
      - name property
      - department property
      - _execute_task internal logic
      
    Coordinates the agent lifecycle and context read/writes.
    """

    def __init__(self, model_name: str = "gemini-2.0-flash", temperature: float = 0.2, llm_adapter: Optional[LLMAdapter] = None):
        self.model_name = model_name
        self.temperature = temperature
        self.status = AgentStatus.IDLE
        self._max_retries = 3
        self.llm_adapter = llm_adapter or LLMAdapter()

    @property
    @abstractmethod
    def name(self) -> str:
        """The identifier name of the agent (e.g. 'Product Lead')."""
        pass

    @property
    @abstractmethod
    def department(self) -> str:
        """The company department this agent belongs to (e.g. 'Planning')."""
        pass

    # ── Lifecycle Hooks ──────────────────────────────────────────────────────

    async def initialize(self, context_manager: ContextManager) -> None:
        """
        Lifecycle step 1: Perform validation on startup preconditions.
        """
        self.status = AgentStatus.INITIALIZING
        logger.debug("agent_lifecycle_init", agent=self.name)
        # Verify context is loaded
        if not context_manager:
            raise AgentInitializationError("ContextManager not provided.")

    @abstractmethod
    async def _execute_task(self, context_manager: ContextManager) -> Dict[str, Any]:
        """
        Internal task executor to be overridden by concrete agent implementations.
        """
        pass

    async def execute(self, context_manager: ContextManager) -> Dict[str, Any]:
        """
        Lifecycle step 2: Execute the core business logic.
        """
        self.status = AgentStatus.RUNNING
        logger.info("agent_lifecycle_execute", agent=self.name, dept=self.department)
        try:
            return await self._execute_task(context_manager)
        except Exception as exc:
            logger.exception("agent_lifecycle_execute_failed", agent=self.name, error=str(exc))
            raise AgentExecutionError(f"Execution failed for agent '{self.name}': {str(exc)}") from exc

    async def validate(self, output_data: Dict[str, Any], context_manager: ContextManager) -> bool:
        """
        Lifecycle step 3: Validate generated output against specifications.
        """
        self.status = AgentStatus.VALIDATING
        logger.debug("agent_lifecycle_validate", agent=self.name)
        # Default implementation checks that output is not empty.
        # Subclasses should override this with schema-specific checks.
        if not output_data:
            raise AgentValidationError(f"Agent '{self.name}' produced empty output data.")
        return True

    async def complete(self, output_data: Dict[str, Any], context_manager: ContextManager) -> AgentResponse:
        """
        Lifecycle step 4: Record output to the Shared Context and return standard response.
        """
        self.status = AgentStatus.COMPLETED
        logger.info("agent_lifecycle_complete", agent=self.name)
        return AgentResponse(
            agent_name=self.name,
            success=True,
            output_data=output_data,
            metrics={"model": self.model_name, "temp": self.temperature}
        )

    async def retry(self, attempt: int, error: Exception, context_manager: ContextManager) -> None:
        """
        Lifecycle step 5: Retry hook. Handles backing off or logging retries.
        """
        self.status = AgentStatus.RETRYING
        logger.warning(
            "agent_lifecycle_retry",
            agent=self.name,
            attempt=attempt,
            max_attempts=self._max_retries,
            error=str(error)
        )
        # Apply slight cooldown before retrying
        await asyncio.sleep(1.0 * attempt)

    async def cleanup(self) -> None:
        """
        Lifecycle step 6: Cleanup runtime files or memory pointers.
        """
        self.status = AgentStatus.IDLE
        logger.debug("agent_lifecycle_cleanup", agent=self.name)

    # ── Orchestrated Run Controller ──────────────────────────────────────────

    async def run(self, context_manager: ContextManager) -> AgentResponse:
        """
        Runs the full lifecycle sequence with built-in retry and recovery loops.
        """
        attempt = 1
        output_data = {}
        
        while attempt <= self._max_retries:
            try:
                # 1. Initialize
                await self.initialize(context_manager)
                
                # Log action to context timeline
                await context_manager.log_agent_action(
                    agent_name=self.name,
                    department=self.department,
                    message=f"Started execution (attempt {attempt})."
                )

                # Acquire write lock
                await context_manager.acquire_lock(self.name)
                
                try:
                    # 2. Execute
                    output_data = await self.execute(context_manager)

                    # 3. Validate
                    await self.validate(output_data, context_manager)
                    
                    # 4. Complete
                    response = await self.complete(output_data, context_manager)
                finally:
                    # Always release write lock
                    context_manager.release_lock(self.name)
                
                await context_manager.log_agent_action(
                    agent_name=self.name,
                    department=self.department,
                    message="Completed task execution successfully."
                )
                
                await self.cleanup()
                return response

            except (AgentInitializationError, AgentExecutionError, AgentValidationError) as exc:
                # Log error details
                await context_manager.log_agent_action(
                    agent_name=self.name,
                    department=self.department,
                    message=f"Error: {str(exc)}"
                )
                
                if attempt == self._max_retries:
                    self.status = AgentStatus.FAILED
                    await self.cleanup()
                    return AgentResponse(
                        agent_name=self.name,
                        success=False,
                        error_message=str(exc),
                        timestamp=datetime.utcnow()
                    )
                
                # 5. Retry
                await self.retry(attempt, exc, context_manager)
                attempt += 1
            
            except Exception as exc:
                # Catch unhandled exceptions as generic execution errors
                self.status = AgentStatus.FAILED
                await context_manager.log_agent_action(
                    agent_name=self.name,
                    department=self.department,
                    message=f"Fatal Unhandled Error: {str(exc)}"
                )
                await self.cleanup()
                return AgentResponse(
                    agent_name=self.name,
                    success=False,
                    error_message=f"Unhandled exception in agent '{self.name}': {str(exc)}",
                    timestamp=datetime.utcnow()
                )
        
        # Fallback if loop ends
        self.status = AgentStatus.FAILED
        await self.cleanup()
        return AgentResponse(
            agent_name=self.name,
            success=False,
            error_message=f"Agent '{self.name}' exceeded maximum retries.",
            timestamp=datetime.utcnow()
        )
