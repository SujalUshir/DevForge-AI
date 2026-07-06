import pytest
from unittest.mock import AsyncMock, MagicMock
from context.manager import ContextManager
from context.schema import ProjectStatus, ExecutionPhase
from agents.llm_adapter import LLMAdapter
from agents.review.engineering_director import EngineeringDirectorAgent
from shared_schemas.review import EngineeringDirectorResponse
from orchestrator.orchestrator import Orchestrator


@pytest.mark.asyncio
async def test_engineering_director_approval():
    ctx_manager = ContextManager.create_new(
        project_name="TestAppDir",
        user_idea="Testing director approval",
        frontend_stack="Next.js",
        backend_stack="FastAPI",
        database_stack="PostgreSQL"
    )

    mock_response = EngineeringDirectorResponse(
        approved=True,
        overall_score=9.5,
        critical_issues=[],
        major_issues=["Add Redis cache for active sessions"],
        minor_issues=["Fix formatting in main.py"],
        missing_sections=[],
        architecture_review="Architecture looks great.",
        engineering_review="REST API spec maps cleanly.",
        security_review="JWT threat model is complete.",
        quality_review="pytest and manual scenarios check.",
        final_recommendations="Approved for deployment.",
        approval_summary="Gate passed. The blueprints are production ready."
    )

    adapter = MagicMock(spec=LLMAdapter)
    adapter.generate_structured_output = AsyncMock(return_value=mock_response)

    agent = EngineeringDirectorAgent(llm_adapter=adapter)
    assert agent.name == "Engineering Director"
    assert agent.department == "Review"

    res = await agent.run(ctx_manager)
    assert res.success is True
    assert res.output_data["approved"] is True

    # Verify context updated
    ctx = ctx_manager.get_context_copy()
    assert ctx.review.approved is True
    assert ctx.review.overall_score == 9.5
    assert ctx.review.critical_issues == []
    assert "Add Redis cache for active sessions" in ctx.review.major_issues
    assert ctx.review.architecture_review == "Architecture looks great."
    assert ctx.review.final_recommendations == "Approved for deployment."


@pytest.mark.asyncio
async def test_engineering_director_rejection_due_to_critical_issues():
    ctx_manager = ContextManager.create_new(
        project_name="TestAppDirReject",
        user_idea="Testing director rejection",
        frontend_stack="Next.js",
        backend_stack="FastAPI",
        database_stack="PostgreSQL"
    )

    mock_response = EngineeringDirectorResponse(
        approved=True,  # LLM tries to approve but it has critical issues
        overall_score=4.0,
        critical_issues=["API routes are missing auth validation checks!"],
        major_issues=[],
        minor_issues=[],
        missing_sections=["database_schema_sql"],
        architecture_review="Incomplete",
        engineering_review="Incomplete",
        security_review="Incomplete",
        quality_review="Incomplete",
        final_recommendations="Fix critical bugs",
        approval_summary="Rejecting due to security risks"
    )

    adapter = MagicMock(spec=LLMAdapter)
    adapter.generate_structured_output = AsyncMock(return_value=mock_response)

    agent = EngineeringDirectorAgent(llm_adapter=adapter)
    res = await agent.run(ctx_manager)
    assert res.success is True
    # The agent should enforce approved = False if there are critical issues
    assert res.output_data["approved"] is False

    # Verify context updated
    ctx = ctx_manager.get_context_copy()
    assert ctx.review.approved is False
    assert "API routes are missing auth validation checks!" in ctx.review.critical_issues
    assert "database_schema_sql" in ctx.review.missing_sections


@pytest.mark.asyncio
async def test_orchestrator_revision_loops_and_retry_limit():
    ctx_manager = ContextManager.create_new(
        project_name="TestRevisionLimit",
        user_idea="Pipeline limit test",
        frontend_stack="Next.js",
        backend_stack="FastAPI",
        database_stack="PostgreSQL"
    )

    # 1. Mock other agents to return success immediately
    mock_agent_response = MagicMock()
    mock_agent_response.success = True
    mock_agent_response.output_data = {}

    # 2. Mock Director to consistently reject the blueprint
    mock_director_response = EngineeringDirectorResponse(
        approved=False,
        overall_score=3.0,
        critical_issues=["Critical flaw present!"],
        major_issues=[],
        minor_issues=[],
        missing_sections=[],
        architecture_review="Flawed",
        engineering_review="Flawed",
        security_review="Flawed",
        quality_review="Flawed",
        final_recommendations="Rewrite",
        approval_summary="Rejecting constantly"
    )

    adapter = MagicMock(spec=LLMAdapter)
    
    async def mock_generate_structured_output(system_instruction, prompt, response_schema, temperature=0.2):
        if response_schema == EngineeringDirectorResponse:
            return mock_director_response
        # For other mock agents if they query Pydantic responses (not applicable since we only register mocks or custom agents)
        return MagicMock()

    adapter.generate_structured_output.side_effect = mock_generate_structured_output

    director_agent = EngineeringDirectorAgent(llm_adapter=adapter)

    # We mock other agents' execution using dummy successful BaseAgent wrappers
    class DummySuccessAgent(MagicMock):
        @property
        def name(self):
            return "Dummy"
        @property
        def department(self):
            return "Planning"
        async def run(self, context_manager):
            res = MagicMock()
            res.success = True
            res.output_data = {"refined_project_name": "Test", "prd_markdown": "prd"}
            return res

    orchestrator = Orchestrator(context_manager=ctx_manager, max_revisions=2)
    
    # Register Dummy success agents for all roles
    for role in ["CEO Agent", "Product Lead", "Market Analyst", "Design Lead", "Principal Architect", 
                 "Backend Lead", "Frontend Lead", "Security Lead", "QA Lead", "Platform Engineer"]:
        agent = DummySuccessAgent()
        # Set name and department properties on agent mock
        type(agent).name = property(lambda self: role)
        type(agent).department = property(lambda self: "Planning")
        orchestrator.register_agent(role, agent)

    # Register the real director agent
    orchestrator.register_agent("Engineering Director", director_agent)

    # Run the full pipeline
    # The pipeline should run, fail the first review, retry, and succeed on the second review (forcing approval)
    success = await orchestrator.execute_pipeline()
    assert success is True

    ctx = ctx_manager.get_context_copy()
    assert ctx.metadata.status == ProjectStatus.COMPLETED
    assert ctx.execution_state.current_phase == ExecutionPhase.COMPLETED
    assert ctx.review.approved is True
    assert len(ctx.review.critical_issues) == 0
    assert any("Critical flaw present!" in issue for issue in ctx.review.major_issues)
