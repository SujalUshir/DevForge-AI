import pytest
from unittest.mock import AsyncMock, MagicMock
from context.manager import ContextManager
from agents.llm_adapter import LLMAdapter
from agents.validation.security_lead import SecurityLeadAgent
from agents.validation.qa_lead import QALeadAgent
from agents.validation.platform_engineer import PlatformEngineerAgent
from shared_schemas.validation import SecurityLeadResponse, QALeadResponse, PlatformEngineerResponse
from orchestrator.orchestrator import Orchestrator


@pytest.mark.asyncio
async def test_security_lead_agent_execution():
    ctx_manager = ContextManager.create_new(
        project_name="TestSec",
        user_idea="Secure app",
        frontend_stack="Next.js",
        backend_stack="FastAPI",
        database_stack="PostgreSQL"
    )

    mock_response = SecurityLeadResponse(
        security_report_markdown="# Security Report\nThreat modeling",
        auth_recommendations="JWT auth",
        authorization_strategy="RBAC",
        secret_management="Env variables",
        owasp_checklist=["Check A", "Check B"],
        api_security="SSL headers",
        input_validation="Pydantic models",
        rate_limiting="100 requests per minute",
        encryption_recommendations="AES-256",
        dependency_risks=["No high risks"],
        owasp_top_10=["CORS header check"], # wait, let's keep it matching checklist
        production_checklist=["Sanitize envs"]
    )

    adapter = MagicMock(spec=LLMAdapter)
    adapter.generate_structured_output = AsyncMock(return_value=mock_response)

    agent = SecurityLeadAgent(llm_adapter=adapter)
    assert agent.name == "Security Lead"
    assert agent.department == "Validation"

    res = await agent.run(ctx_manager)
    assert res.success is True
    assert res.output_data["security_report_markdown"] == "# Security Report\nThreat modeling"

    # Verify context updated
    ctx = ctx_manager.get_context_copy()
    assert ctx.validation.security_report_markdown == mock_response.security_report_markdown
    assert ctx.validation.auth_recommendations == "JWT auth"
    assert ctx.validation.authorization_strategy == "RBAC"
    assert ctx.validation.secret_management == "Env variables"
    assert ctx.validation.owasp_checklist == ["Check A", "Check B"]
    assert ctx.validation.api_security == "SSL headers"
    assert ctx.validation.input_validation == "Pydantic models"
    assert ctx.validation.rate_limiting == "100 requests per minute"
    assert ctx.validation.encryption_recommendations == "AES-256"
    assert ctx.validation.dependency_risks == ["No high risks"]
    assert ctx.validation.production_security_checklist == ["Sanitize envs"]


@pytest.mark.asyncio
async def test_qa_lead_agent_execution():
    ctx_manager = ContextManager.create_new(
        project_name="TestQA",
        user_idea="QA app",
        frontend_stack="Next.js",
        backend_stack="FastAPI",
        database_stack="PostgreSQL"
    )

    mock_response = QALeadResponse(
        test_plan_markdown="# Test Plan\nStrategy details",
        unit_testing_strategy="pytest with mocks",
        integration_tests="Database sandbox",
        api_tests="httpx endpoint checks",
        frontend_testing="Playwright automated runs",
        edge_cases=["Boundary index zero", "Empty file input"],
        acceptance_criteria=["Verify login flow"],
        regression_testing="CI regression runner",
        manual_testing_checklist=["Manual flow check"],
        quality_risks=["Network latency risks"]
    )

    adapter = MagicMock(spec=LLMAdapter)
    adapter.generate_structured_output = AsyncMock(return_value=mock_response)

    agent = QALeadAgent(llm_adapter=adapter)
    assert agent.name == "QA Lead"
    assert agent.department == "Validation"

    res = await agent.run(ctx_manager)
    assert res.success is True
    assert res.output_data["test_plan_markdown"] == "# Test Plan\nStrategy details"

    # Verify context updated
    ctx = ctx_manager.get_context_copy()
    assert ctx.validation.test_plan_markdown == mock_response.test_plan_markdown
    assert ctx.validation.unit_testing_strategy == "pytest with mocks"
    assert ctx.validation.integration_tests == "Database sandbox"
    assert ctx.validation.api_tests == "httpx endpoint checks"
    assert ctx.validation.frontend_testing == "Playwright automated runs"
    assert ctx.validation.edge_cases == ["Boundary index zero", "Empty file input"]
    assert ctx.validation.acceptance_criteria == ["Verify login flow"]
    assert ctx.validation.regression_testing == "CI regression runner"
    assert ctx.validation.manual_testing_checklist == ["Manual flow check"]
    assert ctx.validation.quality_risks == ["Network latency risks"]


@pytest.mark.asyncio
async def test_platform_engineer_agent_execution():
    ctx_manager = ContextManager.create_new(
        project_name="TestPlatform",
        user_idea="Platform deployment",
        frontend_stack="Next.js",
        backend_stack="FastAPI",
        database_stack="PostgreSQL"
    )

    mock_response = PlatformEngineerResponse(
        dockerfile="FROM python:3.11\nWORKDIR /app",
        docker_compose_yml="version: '3.8'\nservices:\n  web:\n    build: .",
        deployment_strategy="Rolling deployments",
        ci_cd_pipeline="GitHub Actions workflows",
        cloud_recommendations="AWS ECS container layout",
        observability="Prometheus tracing APM",
        monitoring="Uptime metric thresholds",
        logging="JSON logger rotator patterns",
        scalability="Horizontal autoscaler CPU 80%",
        backup_strategy="Daily snapshots retention",
        production_readiness=["Ready check A", "Ready check B"]
    )

    adapter = MagicMock(spec=LLMAdapter)
    adapter.generate_structured_output = AsyncMock(return_value=mock_response)

    agent = PlatformEngineerAgent(llm_adapter=adapter)
    assert agent.name == "Platform Engineer"
    assert agent.department == "Validation"

    res = await agent.run(ctx_manager)
    assert res.success is True
    assert res.output_data["dockerfile"] == "FROM python:3.11\nWORKDIR /app"

    # Verify context updated
    ctx = ctx_manager.get_context_copy()
    assert ctx.validation.devops_configs.dockerfile == "FROM python:3.11\nWORKDIR /app"
    assert ctx.validation.devops_configs.docker_compose_yml == "version: '3.8'\nservices:\n  web:\n    build: ."
    assert ctx.validation.deployment_strategy == "Rolling deployments"
    assert ctx.validation.ci_cd_pipeline == "GitHub Actions workflows"
    assert ctx.validation.cloud_recommendations == "AWS ECS container layout"
    assert ctx.validation.observability == "Prometheus tracing APM"
    assert ctx.validation.monitoring == "Uptime metric thresholds"
    assert ctx.validation.logging == "JSON logger rotator patterns"
    assert ctx.validation.scalability == "Horizontal autoscaler CPU 80%"
    assert ctx.validation.backup_strategy == "Daily snapshots retention"
    assert ctx.validation.production_readiness == ["Ready check A", "Ready check B"]


@pytest.mark.asyncio
async def test_validation_department_workflow():
    ctx_manager = ContextManager.create_new(
        project_name="TestValidationWorkflow",
        user_idea="Workflow testing",
        frontend_stack="Next.js",
        backend_stack="FastAPI",
        database_stack="PostgreSQL"
    )

    mock_security = SecurityLeadResponse(
        security_report_markdown="Security report",
        auth_recommendations="Auth recommendations",
        authorization_strategy="Authorization strategy",
        secret_management="Secret management",
        owasp_checklist=["OWASP"],
        api_security="API security",
        input_validation="Input validation",
        rate_limiting="Rate limiting",
        encryption_recommendations="Encryption",
        dependency_risks=["Dependencies"],
        production_checklist=["Production security"]
    )

    mock_qa = QALeadResponse(
        test_plan_markdown="QA report",
        unit_testing_strategy="Unit testing",
        integration_tests="Integration testing",
        api_tests="API testing",
        frontend_testing="Frontend testing",
        edge_cases=["Edge case"],
        acceptance_criteria=["Acceptance criteria"],
        regression_testing="Regression testing",
        manual_testing_checklist=["Manual testing"],
        quality_risks=["Quality risks"]
    )

    mock_platform = PlatformEngineerResponse(
        dockerfile="Dockerfile specs",
        docker_compose_yml="Docker compose specs",
        deployment_strategy="Deployment strategy",
        ci_cd_pipeline="CI/CD specs",
        cloud_recommendations="Cloud recommendations",
        observability="Observability",
        monitoring="Monitoring",
        logging="Logging",
        scalability="Scalability",
        backup_strategy="Backup strategy",
        production_readiness=["Readiness check"]
    )

    adapter = MagicMock(spec=LLMAdapter)
    
    async def mock_generate_structured_output(system_instruction, prompt, response_schema, temperature=0.2):
        if response_schema == SecurityLeadResponse:
            return mock_security
        elif response_schema == QALeadResponse:
            return mock_qa
        elif response_schema == PlatformEngineerResponse:
            return mock_platform
        raise ValueError(f"Unknown schema: {response_schema}")

    adapter.generate_structured_output.side_effect = mock_generate_structured_output

    sec_agent = SecurityLeadAgent(llm_adapter=adapter)
    qa_agent = QALeadAgent(llm_adapter=adapter)
    plat_agent = PlatformEngineerAgent(llm_adapter=adapter)

    orchestrator = Orchestrator(context_manager=ctx_manager)
    orchestrator.register_agent("Security Lead", sec_agent)
    orchestrator.register_agent("QA Lead", qa_agent)
    orchestrator.register_agent("Platform Engineer", plat_agent)

    # Run agents in the orchestrator pipeline
    sec_res = await orchestrator.run_agent_safely("Security Lead")
    qa_res = await orchestrator.run_agent_safely("QA Lead")
    plat_res = await orchestrator.run_agent_safely("Platform Engineer")

    assert sec_res.success is True
    assert qa_res.success is True
    assert plat_res.success is True

    ctx = ctx_manager.get_context_copy()
    assert ctx.validation.security_report_markdown == "Security report"
    assert ctx.validation.test_plan_markdown == "QA report"
    assert ctx.validation.devops_configs.dockerfile == "Dockerfile specs"
