import pytest
import asyncio
from typing import Dict, Any

from context.manager import ContextManager
from context.schema import ProjectStatus, ExecutionPhase
from orchestrator.orchestrator import Orchestrator
from agents.mock_agents import (
    MockProductLead,
    MockMarketAnalyst,
    MockDesignLead,
    MockPrincipalArchitect,
    MockBackendLead,
    MockFrontendLead,
    MockSecurityLead,
    MockQALead,
    MockPlatformEngineer,
    MockEngineeringDirector
)


def register_mock_agents(orchestrator: Orchestrator, director_reject: bool = False):
    """
    Helper to inject mock agents into the orchestrator instance.
    """
    orchestrator.register_agent("Product Lead", MockProductLead())
    orchestrator.register_agent("Market Analyst", MockMarketAnalyst())
    orchestrator.register_agent("Design Lead", MockDesignLead())
    orchestrator.register_agent("Principal Architect", MockPrincipalArchitect())
    orchestrator.register_agent("Backend Lead", MockBackendLead())
    orchestrator.register_agent("Frontend Lead", MockFrontendLead())
    orchestrator.register_agent("Security Lead", MockSecurityLead())
    orchestrator.register_agent("QA Lead", MockQALead())
    orchestrator.register_agent("Platform Engineer", MockPlatformEngineer())
    orchestrator.register_agent("Engineering Director", MockEngineeringDirector(force_reject_once=director_reject))


@pytest.mark.asyncio
async def test_orchestrator_successful_pipeline_run():
    """
    Verify complete sequential and parallel execution of all mock agents in the pipeline.
    """
    ctx_manager = ContextManager.create_new(
        project_name="MockSaaS",
        user_idea="A collaborative tool",
        frontend_stack="Next.js",
        backend_stack="FastAPI",
        database_stack="PostgreSQL"
    )
    
    orchestrator = Orchestrator(context_manager=ctx_manager)
    register_mock_agents(orchestrator, director_reject=False)
    
    # Store events captured during execution
    events = []
    orchestrator.subscribe(lambda event: events.append(event))
    
    # Execute
    success = await orchestrator.execute_pipeline()
    assert success is True
    
    # Check context final states
    ctx = ctx_manager.get_context_copy()
    assert ctx.metadata.status == ProjectStatus.COMPLETED
    assert ctx.execution_state.current_phase == ExecutionPhase.COMPLETED
    assert ctx.planning.prd_markdown != ""
    assert ctx.architecture.topology_markdown != ""
    assert ctx.engineering.api_spec_yaml != ""
    assert ctx.validation.security_report_markdown != ""
    assert ctx.validation.devops_configs.dockerfile != ""
    assert ctx.review.approved is True
    
    # Verify timeline log contains items for each department
    timeline = ctx.execution_state.timeline_logs
    assert len(timeline) > 10
    assert any(log.agent_name == "Product Lead" for log in timeline)
    assert any(log.agent_name == "Principal Architect" for log in timeline)
    assert any(log.agent_name == "Engineering Director" for log in timeline)
    
    # Verify events were emitted correctly
    event_types = [e["event"] for e in events]
    assert "pipeline_started" in event_types
    assert "phase_started" in event_types
    assert "agent_started" in event_types
    assert "agent_completed" in event_types
    assert "pipeline_completed" in event_types


@pytest.mark.asyncio
async def test_orchestrator_revision_loop():
    """
    Verify that the orchestrator enters revision loops when the director rejects a blueprint.
    """
    ctx_manager = ContextManager.create_new(
        project_name="MockSaaS",
        user_idea="A collaborative tool with revision",
        frontend_stack="Next.js",
        backend_stack="FastAPI",
        database_stack="PostgreSQL"
    )
    
    # Director will reject on first pass, approve on second pass
    orchestrator = Orchestrator(context_manager=ctx_manager, max_revisions=2)
    register_mock_agents(orchestrator, director_reject=True)
    
    events = []
    orchestrator.subscribe(lambda event: events.append(event))
    
    success = await orchestrator.execute_pipeline()
    assert success is True
    
    # Verify revision was triggered
    event_types = [e["event"] for e in events]
    assert "revision_triggered" in event_types
    
    ctx = ctx_manager.get_context_copy()
    assert ctx.metadata.status == ProjectStatus.COMPLETED
    assert ctx.review.approved is True  # Second pass approved
