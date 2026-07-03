import pytest
import asyncio
from pathlib import Path
from uuid import UUID

from context.schema import SharedProjectContext, ProjectStatus, ExecutionPhase
from context.manager import ContextManager, ContextLockError


def test_schema_serialization_deserialization():
    """
    Test that schema parses tech stack inputs and serializes/deserializes with expected defaults.
    """
    manager = ContextManager.create_new(
        project_name="TestProject",
        user_idea="A test software application concept",
        frontend_stack="React",
        backend_stack="FastAPI",
        database_stack="PostgreSQL"
    )
    
    context = manager.get_context_copy()
    assert context.metadata.project_name == "TestProject"
    assert context.metadata.user_idea == "A test software application concept"
    assert context.metadata.tech_stack.frontend == "React"
    assert context.metadata.tech_stack.backend == "FastAPI"
    assert context.metadata.tech_stack.database == "PostgreSQL"
    assert isinstance(context.metadata.project_id, UUID)
    assert context.metadata.status == ProjectStatus.PENDING
    
    # Verify serialization roundtrip
    dumped = context.model_dump_json()
    loaded = SharedProjectContext.model_validate_json(dumped)
    assert loaded.metadata.project_id == context.metadata.project_id


@pytest.mark.asyncio
async def test_context_manager_locking_and_safety(tmp_path):
    """
    Test context locking mechanism, verifying lockless writes are denied and locked updates succeed.
    """
    manager = ContextManager.create_new(
        project_name="TestProject",
        user_idea="Testing locking patterns",
        frontend_stack="Next.js",
        backend_stack="FastAPI",
        database_stack="SQLite",
        persist_dir=tmp_path
    )
    
    # 1. Attempt updating without lock must fail
    def update_prd(planning_slice):
        planning_slice.prd_markdown = "Test PRD Content"

    with pytest.raises(ContextLockError):
        await manager.update_planning(agent_name="Product Lead", update_fn=update_prd)

    # 2. Acquire lock and run modification
    await manager.acquire_lock("Product Lead")
    await manager.update_planning(agent_name="Product Lead", update_fn=update_prd)
    
    # Verify change
    updated_context = manager.get_context_copy()
    assert updated_context.planning.prd_markdown == "Test PRD Content"
    
    # Verify file persistence
    persist_file = tmp_path / f"context_{updated_context.metadata.project_id}.json"
    assert persist_file.exists()
    
    # Read and inspect persisted json file contents
    loaded_manager = ContextManager.load_from_file(persist_file)
    assert loaded_manager.get_context_copy().planning.prd_markdown == "Test PRD Content"

    # 3. Attempt releasing lock using wrong owner should fail
    with pytest.raises(ContextLockError):
        manager.release_lock("Architect Lead")

    # 4. Release lock with correct owner and verify unlock
    manager.release_lock("Product Lead")
    
    # Attempting write again after release should fail
    with pytest.raises(ContextLockError):
        await manager.update_planning(agent_name="Product Lead", update_fn=update_prd)


@pytest.mark.asyncio
async def test_execution_timeline_logging(tmp_path):
    """
    Test helper method for log ingestion and audit trail logs.
    """
    manager = ContextManager.create_new(
        project_name="TestProject",
        user_idea="Testing logs",
        frontend_stack="Next.js",
        backend_stack="FastAPI",
        database_stack="SQLite",
        persist_dir=tmp_path
    )
    
    await manager.log_agent_action(
        agent_name="CEO",
        department="Management",
        message="Initialized project forge execution pipeline."
    )
    
    context = manager.get_context_copy()
    logs = context.execution_state.timeline_logs
    assert len(logs) == 1
    assert logs[0].agent_name == "CEO"
    assert logs[0].department == "Management"
    assert logs[0].message == "Initialized project forge execution pipeline."
