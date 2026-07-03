"""
Orchestration Engine.

Manages execution lifecycle phases, coordinating task delegation, sequential
department execution, parallel validation gates, context locking, and
revision loop retries.
"""

import asyncio
from typing import Callable, Dict, List, Any, Optional
import structlog

from context.schema import ExecutionPhase, ProjectStatus
from context.manager import ContextManager
from agents.base import BaseAgent
from agents.models import AgentResponse

logger = structlog.get_logger(__name__)


class Orchestrator:
    """
    Main Multi-Agent pipeline orchestrator.
    Controls phase gating, lock synchronization, and event emission.
    """

    def __init__(self, context_manager: ContextManager, max_revisions: int = 2):
        self.context_manager = context_manager
        self.max_revisions = max_revisions
        self._subscribers: List[Callable[[Dict[str, Any]], None]] = []
        
        # Injected agent maps to support easy unit testing and mock/real swappability
        self.agents: Dict[str, BaseAgent] = {}

    def register_agent(self, role_name: str, agent: BaseAgent) -> None:
        """
        Inject an agent instance for a specific company role.
        """
        self.agents[role_name] = agent
        logger.debug("orchestrator_agent_registered", role=role_name, agent=agent.__class__.__name__)

    def subscribe(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Subscribe to execution and state change event streams (e.g. for SSE streams).
        """
        self._subscribers.append(callback)

    def emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Broadcasts status updates to all registered subscribers.
        """
        payload = {
            "event": event_type,
            "data": data,
            "project_id": str(self.context_manager.get_context_copy().metadata.project_id)
        }
        for sub in self._subscribers:
            try:
                sub(payload)
            except Exception as exc:
                logger.error("subscriber_notification_error", error=str(exc))

    async def run_agent_safely(self, agent_name: str) -> AgentResponse:
        """
        Retrieves agent from registry, acquires context lock, runs execution,
        emits log events, and releases the lock cleanly on completion/error.
        """
        agent = self.agents.get(agent_name)
        if not agent:
            raise ValueError(f"Agent '{agent_name}' has not been registered in the orchestrator.")

        # Update active agents execution state list
        def add_active_agent(state):
            if agent_name not in state.active_agents:
                state.active_agents.append(agent_name)
        
        # Need lock to update active agents list
        await self.context_manager.acquire_lock("CEO")
        await self.context_manager.update_execution_state("CEO", add_active_agent)
        self.context_manager.release_lock("CEO")

        self.emit_event("agent_started", {"agent": agent_name, "dept": agent.department})

        # Run agent - it manages its own internal lifecycle and locks when writing
        response = await agent.run(self.context_manager)

        # Remove from active agents
        def remove_active_agent(state):
            if agent_name in state.active_agents:
                state.active_agents.remove(agent_name)
                
        await self.context_manager.acquire_lock("CEO")
        await self.context_manager.update_execution_state("CEO", remove_active_agent)
        self.context_manager.release_lock("CEO")

        if response.success:
            self.emit_event("agent_completed", {"agent": agent_name, "data": response.output_data})
        else:
            self.emit_event("agent_failed", {"agent": agent_name, "error": response.error_message})

        return response

    async def execute_pipeline(self) -> bool:
        """
        Coordinates full multi-department pipeline workflow execution.
        """
        await self.context_manager.log_agent_action("CEO", "Management", "Starting execution pipeline.")
        self.emit_event("pipeline_started", {})

        # Set status to PROCESSING
        await self.context_manager.acquire_lock("CEO")
        await self.context_manager.update_project_status("CEO", ProjectStatus.PROCESSING)
        self.context_manager.release_lock("CEO")

        revision_count = 0

        while revision_count <= self.max_revisions:
            # ── 1. PLANNING PHASE ────────────────────────────────────────────
            await self.context_manager.acquire_lock("CEO")
            await self.context_manager.set_active_phase("CEO", ExecutionPhase.PLANNING)
            self.context_manager.release_lock("CEO")
            self.emit_event("phase_started", {"phase": ExecutionPhase.PLANNING})
            
            # Runs planning agents in parallel
            planning_tasks = [
                self.run_agent_safely("Product Lead"),
                self.run_agent_safely("Market Analyst"),
                self.run_agent_safely("Design Lead")
            ]
            planning_responses = await asyncio.gather(*planning_tasks)
            if any(not r.success for r in planning_responses):
                await self._fail_pipeline("Planning phase failed.")
                return False

            # ── 2. ARCHITECTURE PHASE ────────────────────────────────────────
            await self.context_manager.acquire_lock("CEO")
            await self.context_manager.set_active_phase("CEO", ExecutionPhase.ARCHITECTURE)
            self.context_manager.release_lock("CEO")
            self.emit_event("phase_started", {"phase": ExecutionPhase.ARCHITECTURE})

            arch_response = await self.run_agent_safely("Principal Architect")
            if not arch_response.success:
                await self._fail_pipeline("Architecture phase failed.")
                return False

            # ── 3. ENGINEERING PHASE ─────────────────────────────────────────
            await self.context_manager.acquire_lock("CEO")
            await self.context_manager.set_active_phase("CEO", ExecutionPhase.ENGINEERING)
            self.context_manager.release_lock("CEO")
            self.emit_event("phase_started", {"phase": ExecutionPhase.ENGINEERING})

            engineering_tasks = [
                self.run_agent_safely("Backend Lead"),
                self.run_agent_safely("Frontend Lead")
            ]
            eng_responses = await asyncio.gather(*engineering_tasks)
            if any(not r.success for r in eng_responses):
                await self._fail_pipeline("Engineering phase failed.")
                return False

            # ── 4. VALIDATION PHASE ──────────────────────────────────────────
            await self.context_manager.acquire_lock("CEO")
            await self.context_manager.set_active_phase("CEO", ExecutionPhase.VALIDATION)
            self.context_manager.release_lock("CEO")
            self.emit_event("phase_started", {"phase": ExecutionPhase.VALIDATION})

            validation_tasks = [
                self.run_agent_safely("Security Lead"),
                self.run_agent_safely("QA Lead"),
                self.run_agent_safely("Platform Engineer")
            ]
            val_responses = await asyncio.gather(*validation_tasks)
            if any(not r.success for r in val_responses):
                await self._fail_pipeline("Validation phase failed.")
                return False

            # ── 5. REVIEW PHASE ──────────────────────────────────────────────
            await self.context_manager.acquire_lock("CEO")
            await self.context_manager.set_active_phase("CEO", ExecutionPhase.REVIEW)
            self.context_manager.release_lock("CEO")
            self.emit_event("phase_started", {"phase": ExecutionPhase.REVIEW})

            review_response = await self.run_agent_safely("Engineering Director")
            if not review_response.success:
                await self._fail_pipeline("Director review failed to execute.")
                return False

            # Check approval gate
            approved = review_response.output_data.get("approved", False)
            if approved:
                # Execution Completed Successfully!
                await self._complete_pipeline()
                return True
            else:
                revision_count += 1
                feedback = review_response.output_data.get("reviewer_feedback", [])
                logger.warning("director_rejected_blueprint", revision=revision_count, max=self.max_revisions, feedback=feedback)
                
                await self.context_manager.log_agent_action(
                    "CEO", 
                    "Management", 
                    f"Director rejected blueprint. Revision loop {revision_count}/{self.max_revisions}. Feedback: {feedback}"
                )
                self.emit_event("revision_triggered", {"revision": revision_count, "feedback": feedback})
                
                if revision_count > self.max_revisions:
                    await self._fail_pipeline(f"Exceeded maximum revision attempts: {self.max_revisions}.")
                    return False

        return False

    async def _complete_pipeline(self) -> None:
        """
        Transition pipeline and context to success state.
        """
        await self.context_manager.acquire_lock("CEO")
        await self.context_manager.set_active_phase("CEO", ExecutionPhase.COMPLETED)
        await self.context_manager.update_project_status("CEO", ProjectStatus.COMPLETED)
        
        # Set execution end time metrics
        from datetime import datetime
        def set_end_time(state):
            state.metrics.end_time = datetime.utcnow()
        await self.context_manager.update_execution_state("CEO", set_end_time)
        
        self.context_manager.release_lock("CEO")

        await self.context_manager.log_agent_action("CEO", "Management", "Orchestration pipeline completed successfully.")
        self.emit_event("pipeline_completed", {})

    async def _fail_pipeline(self, error_msg: str) -> None:
        """
        Transition pipeline and context to failure state.
        """
        await self.context_manager.acquire_lock("CEO")
        await self.context_manager.set_active_phase("CEO", ExecutionPhase.FAILED)
        await self.context_manager.update_project_status("CEO", ProjectStatus.FAILED)
        self.context_manager.release_lock("CEO")

        await self.context_manager.log_agent_action("CEO", "Management", f"Pipeline failed: {error_msg}")
        self.emit_event("pipeline_failed", {"error": error_msg})
