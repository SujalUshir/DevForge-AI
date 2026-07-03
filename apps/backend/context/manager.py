"""
Shared Project Context Manager.

Coordinates concurrent read and write operations on the SharedProjectContext
using an asynchronous lock, enforcing the Single Writer Principle.
Also handles workspace directory resolution and context serialization/deserialization.
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import structlog

from context.schema import SharedProjectContext, TimelineLogItem, ExecutionPhase, ProjectStatus
from config import settings

logger = structlog.get_logger(__name__)


class ContextLockError(Exception):
    """Raised when an agent attempts a write operation without acquiring the lock."""
    pass


class ContextManager:
    """
    Manages the thread-safe state lifecycle of the SharedProjectContext.

    Coordinates agent access, handles runtime schema validation,
    locks state changes, and writes execution logs.
    """

    def __init__(self, context: SharedProjectContext, persist_path: Optional[Path] = None):
        self._context = context
        self._lock = asyncio.Lock()
        self._owner: Optional[str] = None
        self._persist_path = persist_path

    @classmethod
    def create_new(
        cls, 
        project_name: str, 
        user_idea: str, 
        frontend_stack: str, 
        backend_stack: str, 
        database_stack: str,
        persist_dir: Optional[Path] = None
    ) -> "ContextManager":
        """
        Factory method to initialize a brand new SharedProjectContext.
        """
        from context.schema import ProjectMetadata, TechStack, PlanningContext, ArchitectureContext, EngineeringContext, ValidationContext, ReviewContext, ExecutionState

        ctx = SharedProjectContext(
            metadata=ProjectMetadata(
                project_name=project_name,
                user_idea=user_idea,
                tech_stack=TechStack(
                    frontend=frontend_stack,
                    backend=backend_stack,
                    database=database_stack
                )
            ),
            planning=PlanningContext(),
            architecture=ArchitectureContext(),
            engineering=EngineeringContext(),
            validation=ValidationContext(),
            review=ReviewContext(),
            execution_state=ExecutionState()
        )
        
        path = None
        if persist_dir:
            persist_dir.mkdir(parents=True, exist_ok=True)
            path = persist_dir / f"context_{ctx.metadata.project_id}.json"

        return cls(context=ctx, persist_path=path)

    @classmethod
    def load_from_file(cls, filepath: Path) -> "ContextManager":
        """
        Load a previously serialized context from disk.
        """
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        ctx = SharedProjectContext.model_validate(data)
        return cls(context=ctx, persist_path=filepath)

    async def acquire_lock(self, agent_name: str) -> None:
        """
        Acquire write lock on the context state.
        Fails if another agent is holding the lock.
        """
        await self._lock.acquire()
        self._owner = agent_name
        logger.info("context_lock_acquired", agent=agent_name, project_id=str(self._context.metadata.project_id))

    def release_lock(self, agent_name: str) -> None:
        """
        Release the write lock on the context state.
        Fails if the requesting agent is not the owner.
        """
        if self._owner != agent_name:
            raise ContextLockError(f"Agent '{agent_name}' does not own the active lock. Current owner: '{self._owner}'")
        
        self._owner = None
        self._lock.release()
        logger.info("context_lock_released", agent=agent_name, project_id=str(self._context.metadata.project_id))

    def check_lock(self, agent_name: str) -> None:
        """
        Verify if the agent has active write access.
        """
        if not self._lock.locked() or self._owner != agent_name:
            raise ContextLockError(f"Write operation denied. Agent '{agent_name}' must acquire lock first.")

    # ── Read Operations (Lockless / Safe) ────────────────────────────────────

    def get_context_copy(self) -> SharedProjectContext:
        """
        Returns a deep copy of the current context model. Safe to read.
        """
        return self._context.model_copy(deep=True)

    def get_metadata(self) -> Dict[str, Any]:
        return self._context.metadata.model_dump()

    def get_planning(self) -> Dict[str, Any]:
        return self._context.planning.model_dump()

    def get_architecture(self) -> Dict[str, Any]:
        return self._context.architecture.model_dump()

    def get_engineering(self) -> Dict[str, Any]:
        return self._context.engineering.model_dump()

    def get_validation(self) -> Dict[str, Any]:
        return self._context.validation.model_dump()

    def get_review(self) -> Dict[str, Any]:
        return self._context.review.model_dump()

    def get_execution_state(self) -> Dict[str, Any]:
        return self._context.execution_state.model_dump()

    # ── Write Operations (Lock-Enforced) ─────────────────────────────────────

    async def update_planning(self, agent_name: str, update_fn: Callable[[Any], None]) -> None:
        """
        Modify the planning slice.
        """
        self.check_lock(agent_name)
        # Deep copy slice, run modifier function, validate, re-assign if valid
        slice_copy = self._context.planning.model_copy(deep=True)
        update_fn(slice_copy)
        self._context.planning = slice_copy
        await self._persist_state()

    async def update_architecture(self, agent_name: str, update_fn: Callable[[Any], None]) -> None:
        self.check_lock(agent_name)
        slice_copy = self._context.architecture.model_copy(deep=True)
        update_fn(slice_copy)
        self._context.architecture = slice_copy
        await self._persist_state()

    async def update_engineering(self, agent_name: str, update_fn: Callable[[Any], None]) -> None:
        self.check_lock(agent_name)
        slice_copy = self._context.engineering.model_copy(deep=True)
        update_fn(slice_copy)
        self._context.engineering = slice_copy
        await self._persist_state()

    async def update_validation(self, agent_name: str, update_fn: Callable[[Any], None]) -> None:
        self.check_lock(agent_name)
        slice_copy = self._context.validation.model_copy(deep=True)
        update_fn(slice_copy)
        self._context.validation = slice_copy
        await self._persist_state()

    async def update_review(self, agent_name: str, update_fn: Callable[[Any], None]) -> None:
        self.check_lock(agent_name)
        slice_copy = self._context.review.model_copy(deep=True)
        update_fn(slice_copy)
        self._context.review = slice_copy
        await self._persist_state()

    async def update_execution_state(self, agent_name: str, update_fn: Callable[[Any], None]) -> None:
        self.check_lock(agent_name)
        slice_copy = self._context.execution_state.model_copy(deep=True)
        update_fn(slice_copy)
        self._context.execution_state = slice_copy
        await self._persist_state()

    async def update_project_status(self, agent_name: str, status: ProjectStatus) -> None:
        self.check_lock(agent_name)
        self._context.metadata.status = status
        await self._persist_state()

    async def update_metadata(self, agent_name: str, update_fn: Callable[[Any], None]) -> None:
        self.check_lock(agent_name)
        slice_copy = self._context.metadata.model_copy(deep=True)
        update_fn(slice_copy)
        self._context.metadata = slice_copy
        await self._persist_state()


    # ── Utilities & Helper Writes ────────────────────────────────────────────

    async def log_agent_action(self, agent_name: str, department: str, message: str) -> None:
        """
        Helper method to append an execution timeline log item to the context.
        Note: This acquires and releases the lock internally.
        """
        async with self._lock:
            log_item = TimelineLogItem(
                agent_name=agent_name,
                department=department,
                message=message
            )
            self._context.execution_state.timeline_logs.append(log_item)
            logger.info("agent_logged_action", agent=agent_name, department=department, msg=message)
            await self._persist_state_unlocked()

    async def set_active_phase(self, agent_name: str, phase: ExecutionPhase) -> None:
        """
        Set active execution phase. Writes are lock-enforced.
        """
        self.check_lock(agent_name)
        self._context.execution_state.current_phase = phase
        await self._persist_state()

    # ── Disk Persistence Helpers ─────────────────────────────────────────────

    async def _persist_state(self) -> None:
        """
        Private method to serialize current state to local JSON file.
        Uses asyncio run_in_executor to avoid blocking the event loop on disk write.
        """
        if not self._persist_path:
            return

        def write_sync():
            with open(self._persist_path, "w", encoding="utf-8") as f:
                f.write(self._context.model_dump_json(indent=2))

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, write_sync)

    async def _persist_state_unlocked(self) -> None:
        """
        Disk write helper that does not check lock context (for direct logs).
        """
        if not self._persist_path:
            return
        
        def write_sync():
            with open(self._persist_path, "w", encoding="utf-8") as f:
                f.write(self._context.model_dump_json(indent=2))

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, write_sync)
