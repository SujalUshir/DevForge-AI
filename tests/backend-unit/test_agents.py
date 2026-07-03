import pytest
from typing import Dict, Any
from datetime import datetime

from context.manager import ContextManager
from agents.base import BaseAgent
from agents.models import AgentStatus, AgentResponse
from agents.registry import agent_registry
from agents.exceptions import AgentValidationError


# Mock agent to test lifecycle behavior
class MockPlanningAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "Mock Product Lead"

    @property
    def department(self) -> str:
        return "Planning"

    async def _execute_task(self, context_manager: ContextManager) -> Dict[str, Any]:
        return {"prd_markdown": "# Mock Project functional specifications"}


class MockFailingAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self._max_retries = 2
        self.execute_calls = 0

    @property
    def name(self) -> str:
        return "Mock Failing Agent"

    @property
    def department(self) -> str:
        return "Validation"

    async def _execute_task(self, context_manager: ContextManager) -> Dict[str, Any]:
        self.execute_calls += 1
        raise ValueError("Simulated network outage or model error")


@pytest.mark.asyncio
async def test_agent_lifecycle_success():
    """
    Test standard agent lifecycle run pipeline (init -> execute -> validate -> complete -> cleanup).
    """
    ctx_manager = ContextManager.create_new(
        project_name="TestApp",
        user_idea="Testing lifecycle",
        frontend_stack="Next",
        backend_stack="FastAPI",
        database_stack="SQLite"
    )
    
    agent = MockPlanningAgent()
    assert agent.status == AgentStatus.IDLE
    
    response = await agent.run(ctx_manager)
    assert response.success is True
    assert response.agent_name == "Mock Product Lead"
    assert response.output_data == {"prd_markdown": "# Mock Project functional specifications"}
    assert agent.status == AgentStatus.IDLE  # Restored to IDLE during cleanup


@pytest.mark.asyncio
async def test_agent_lifecycle_retry_failure():
    """
    Test that agent runs execution retry loops and terminates cleanly with failed response status.
    """
    ctx_manager = ContextManager.create_new(
        project_name="TestApp",
        user_idea="Testing lifecycle retries",
        frontend_stack="Next",
        backend_stack="FastAPI",
        database_stack="SQLite"
    )
    
    agent = MockFailingAgent()
    response = await agent.run(ctx_manager)
    
    assert response.success is False
    assert agent.execute_calls == 2  # Max retries set to 2 in constructor
    assert "ValueError" in response.error_message or "Simulated" in response.error_message


def test_agent_registry_decorator():
    """
    Test agent class decorator registration.
    """
    registry_len_before = len(agent_registry.get_all_registered_names())
    
    @agent_registry.register
    class TempRegisteredAgent(BaseAgent):
        @property
        def name(self) -> str:
            return "Temp Registered Agent"
        @property
        def department(self) -> str:
            return "Engineering"
        async def _execute_task(self, context_manager: ContextManager) -> Dict[str, Any]:
            return {}

    assert "Temp Registered Agent" in agent_registry.get_all_registered_names()
    assert agent_registry.get_agent_class("Temp Registered Agent") == TempRegisteredAgent
