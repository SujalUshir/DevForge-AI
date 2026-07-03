import pytest
from pydantic import BaseModel, Field
from typing import List

from context.manager import ContextManager
from context.schema import ProjectStatus
from agents.llm_adapter import LLMAdapter
from agents.ceo import CEOAgent, CEOResponseSchema


class DummySchema(BaseModel):
    title: str = Field(..., description="A simple text title.")
    score: int = Field(..., description="Score rating value.")


@pytest.mark.asyncio
async def test_llm_adapter_mock_generation():
    """
    Test that LLMAdapter mock generation creates schema-compliant Pydantic models.
    """
    adapter = LLMAdapter(api_key="")  # force mock mode
    assert adapter.mock_mode is True

    result: DummySchema = await adapter.generate_structured_output(
        system_instruction="You are a reviewer helper.",
        prompt="Review output score",
        response_schema=DummySchema
    )

    assert isinstance(result, DummySchema)
    assert result.title != ""
    assert isinstance(result.score, int)


@pytest.mark.asyncio
async def test_ceo_agent_execution_with_mock_adapter():
    """
    Test that CEOAgent executes cleanly under base agent execution locks and updates root metadata.
    """
    ctx_manager = ContextManager.create_new(
        project_name="LegacyApp",
        user_idea="A project planning assistant dashboard",
        frontend_stack="React",
        backend_stack="Django",
        database_stack="MySQL"
    )

    # Inject mock adapter to ensure deterministic response
    adapter = LLMAdapter(api_key="")
    
    agent = CEOAgent(llm_adapter=adapter)
    
    # Verify metadata before run
    meta_before = ctx_manager.get_metadata()
    assert meta_before["project_name"] == "LegacyApp"
    assert meta_before["tech_stack"]["frontend"] == "React"

    # Run agent under base agent executor (run method handles locking internally)
    response = await agent.run(ctx_manager)
    
    assert response.success is True
    assert "refined_project_name" in response.output_data
    
    # Verify metadata after run (was updated via update_metadata slice)
    meta_after = ctx_manager.get_metadata()
    assert meta_after["project_name"] == "Mock Generated structured output string placeholder"
    assert meta_after["tech_stack"]["frontend"] == "Mock Generated structured output string placeholder"
    assert meta_after["tech_stack"]["backend"] == "Mock Generated structured output string placeholder"
    assert meta_after["tech_stack"]["database"] == "Mock Generated structured output string placeholder"
