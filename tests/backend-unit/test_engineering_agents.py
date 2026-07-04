import pytest
from unittest.mock import AsyncMock, MagicMock
from context.manager import ContextManager
from agents.llm_adapter import LLMAdapter
from agents.engineering.backend_lead import BackendLeadAgent
from agents.engineering.frontend_lead import FrontendLeadAgent
from shared_schemas.engineering import BackendLeadResponse, FrontendLeadResponse
from orchestrator.orchestrator import Orchestrator


@pytest.mark.asyncio
async def test_backend_lead_agent_execution():
    ctx_manager = ContextManager.create_new(
        project_name="TestBackend",
        user_idea="FastAPI backend",
        frontend_stack="Next.js",
        backend_stack="FastAPI",
        database_stack="PostgreSQL"
    )

    mock_response = BackendLeadResponse(
        backend_architecture="Microservices architecture",
        backend_services=["AuthService", "ProductService"],
        api_design="GET /users, POST /users",
        api_spec_yaml="openapi: 3.0.0\ninfo:\n  title: Test Backend\n  version: 1.0.0",
        database_schema_sql="CREATE TABLE users (id UUID PRIMARY KEY);",
        backend_main_py="from fastapi import FastAPI\napp = FastAPI()",
        database_notes="Use index on users table",
        folder_structure="src/\n  main.py",
        security_notes="JWT Authentication",
        dependencies=["fastapi", "uvicorn"]
    )

    adapter = MagicMock(spec=LLMAdapter)
    adapter.generate_structured_output = AsyncMock(return_value=mock_response)

    agent = BackendLeadAgent(llm_adapter=adapter)
    assert agent.name == "Backend Lead"
    assert agent.department == "Engineering"

    res = await agent.run(ctx_manager)
    assert res.success is True
    assert res.output_data["backend_architecture"] == "Microservices architecture"

    # Verify context updated
    ctx = ctx_manager.get_context_copy()
    assert ctx.engineering.api_spec_yaml == mock_response.api_spec_yaml
    assert ctx.engineering.database_schema_sql == mock_response.database_schema_sql
    assert ctx.engineering.backend_architecture == "Microservices architecture"
    assert ctx.engineering.backend_services == ["AuthService", "ProductService"]
    assert ctx.engineering.api_design == "GET /users, POST /users"
    assert ctx.engineering.database_notes == "Use index on users table"
    assert ctx.engineering.folder_structure_backend == "src/\n  main.py"
    assert ctx.engineering.security_notes == "JWT Authentication"


@pytest.mark.asyncio
async def test_frontend_lead_agent_execution():
    ctx_manager = ContextManager.create_new(
        project_name="TestFrontend",
        user_idea="Next.js app",
        frontend_stack="Next.js",
        backend_stack="FastAPI",
        database_stack="PostgreSQL"
    )

    mock_response = FrontendLeadResponse(
        frontend_architecture="Next.js App Router layout patterns",
        frontend_pages=["Dashboard page", "Settings page"],
        routing="Router path structure config",
        components=["Navbar component", "Sidebar component"],
        layout="Design system layout components map",
        state_management="React Context and hooks",
        styling_approach="Vanilla CSS styling system",
        accessibility_checklist=["Screen reader labels", "Keyboard accessible"],
        responsive_design="Tailored spacing grids",
        folder_structure="app/\n  page.tsx"
    )

    adapter = MagicMock(spec=LLMAdapter)
    adapter.generate_structured_output = AsyncMock(return_value=mock_response)

    agent = FrontendLeadAgent(llm_adapter=adapter)
    assert agent.name == "Frontend Lead"
    assert agent.department == "Engineering"

    res = await agent.run(ctx_manager)
    assert res.success is True
    assert res.output_data["frontend_architecture"] == "Next.js App Router layout patterns"

    # Verify context updated
    ctx = ctx_manager.get_context_copy()
    assert ctx.engineering.frontend_architecture == "Next.js App Router layout patterns"
    assert ctx.engineering.frontend_pages == ["Dashboard page", "Settings page"]
    assert ctx.engineering.routing == "Router path structure config"
    assert ctx.engineering.components == ["Navbar component", "Sidebar component"]
    assert ctx.engineering.layout == "Design system layout components map"
    assert ctx.engineering.state_management == "React Context and hooks"
    assert ctx.engineering.styling_approach == "Vanilla CSS styling system"
    assert ctx.engineering.accessibility_checklist == ["Screen reader labels", "Keyboard accessible"]
    assert ctx.engineering.responsive_design == "Tailored spacing grids"
    assert ctx.engineering.folder_structure_frontend == "app/\n  page.tsx"


@pytest.mark.asyncio
async def test_engineering_department_workflow():
    ctx_manager = ContextManager.create_new(
        project_name="TestWorkflow",
        user_idea="Full stack app",
        frontend_stack="Next.js",
        backend_stack="FastAPI",
        database_stack="PostgreSQL"
    )

    mock_backend = BackendLeadResponse(
        backend_architecture="Service architecture",
        backend_services=["ServiceA"],
        api_design="REST Endpoints",
        api_spec_yaml="openapi: 3.0.0",
        database_schema_sql="CREATE TABLE users;",
        backend_main_py="app = FastAPI()",
        database_notes="Index details",
        folder_structure="workspace",
        security_notes="OAuth2",
        dependencies=["fastapi"]
    )

    mock_frontend = FrontendLeadResponse(
        frontend_architecture="Component layout",
        frontend_pages=["Dashboard"],
        routing="/dashboard",
        components=["Button"],
        layout="Flex grid layout",
        state_management="Redux",
        styling_approach="Tailwind CSS",
        accessibility_checklist=["ARIA standards"],
        responsive_design="Desktop first",
        folder_structure="components"
    )

    adapter = MagicMock(spec=LLMAdapter)
    
    async def mock_generate_structured_output(system_instruction, prompt, response_schema, temperature=0.2):
        if response_schema == BackendLeadResponse:
            return mock_backend
        elif response_schema == FrontendLeadResponse:
            return mock_frontend
        raise ValueError(f"Unknown schema: {response_schema}")

    adapter.generate_structured_output.side_effect = mock_generate_structured_output

    backend_agent = BackendLeadAgent(llm_adapter=adapter)
    frontend_agent = FrontendLeadAgent(llm_adapter=adapter)

    orchestrator = Orchestrator(context_manager=ctx_manager)
    orchestrator.register_agent("Backend Lead", backend_agent)
    orchestrator.register_agent("Frontend Lead", frontend_agent)

    # Run both agents in the orchestrator pipeline
    backend_res = await orchestrator.run_agent_safely("Backend Lead")
    frontend_res = await orchestrator.run_agent_safely("Frontend Lead")

    assert backend_res.success is True
    assert frontend_res.success is True

    ctx = ctx_manager.get_context_copy()
    assert ctx.engineering.backend_architecture == "Service architecture"
    assert ctx.engineering.frontend_architecture == "Component layout"
