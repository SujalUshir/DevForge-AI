"""
Pydantic schemas for the Validation Department agents.
"""

from pydantic import BaseModel, Field
from typing import List


class SecurityLeadResponse(BaseModel):
    """
    Structured JSON output schema for Security Lead Agent.
    """
    security_report_markdown: str = Field(
        ...,
        description="The main threat modeling and security assessment report in Markdown."
    )
    auth_recommendations: str = Field(
        ...,
        description="Detailed recommendations for user authentication schemas."
    )
    authorization_strategy: str = Field(
        ...,
        description="RBAC rules, scope permissions, and user authorization structures."
    )
    secret_management: str = Field(
        ...,
        description="Secret manager integrations and config injection guidelines."
    )
    owasp_checklist: List[str] = Field(
        ...,
        description="Checklist validating protection against OWASP Top 10 vulnerabilities."
    )
    api_security: str = Field(
        ...,
        description="HTTPS setup, CORS policies, rate limiting, and header protections."
    )
    input_validation: str = Field(
        ...,
        description="Data validation specifications, schemas enforcement, and sanitization."
    )
    rate_limiting: str = Field(
        ...,
        description="Details on request limits, thresholds, and server rules."
    )
    encryption_recommendations: str = Field(
        ...,
        description="Guidelines for encrypting database tables and secure transit layers."
    )
    dependency_risks: List[str] = Field(
        ...,
        description="Vulnerabilities or audit issues identified in direct dependency libraries."
    )
    production_checklist: List[str] = Field(
        ...,
        description="Verification guidelines for production environment safety validation."
    )


class QALeadResponse(BaseModel):
    """
    Structured JSON output schema for QA Lead Agent.
    """
    test_plan_markdown: str = Field(
        ...,
        description="Comprehensive testing strategy and test plan in clean Markdown format."
    )
    unit_testing_strategy: str = Field(
        ...,
        description="Mocking rules, test coverage goals, and frameworks (e.g. pytest)."
    )
    integration_tests: str = Field(
        ...,
        description="Details on database testing boundaries and service-to-service validation."
    )
    api_tests: str = Field(
        ...,
        description="HTTP response codes, path parameters, and endpoint verification scenarios."
    )
    frontend_testing: str = Field(
        ...,
        description="Strategies for component verification and E2E (e.g. Cypress, Playwright)."
    )
    edge_cases: List[str] = Field(
        ...,
        description="List of specific boundary states, invalid inputs, and stress conditions."
    )
    acceptance_criteria: List[str] = Field(
        ...,
        description="User stories validation checkpoints verifying completeness."
    )
    regression_testing: str = Field(
        ...,
        description="Automation triggers and checks to maintain compatibility."
    )
    manual_testing_checklist: List[str] = Field(
        ...,
        description="A step-by-step checklist to guide manual verification runs."
    )
    quality_risks: List[str] = Field(
        ...,
        description="Critical failure mechanisms or potential UX flaws identified."
    )


class PlatformEngineerResponse(BaseModel):
    """
    Structured JSON output schema for Platform Engineer Agent.
    """
    dockerfile: str = Field(
        ...,
        description="A complete, valid Dockerfile skeleton matching the environment."
    )
    docker_compose_yml: str = Field(
        ...,
        description="A complete, valid docker-compose.yml configuration setup."
    )
    deployment_strategy: str = Field(
        ...,
        description="Details on release cycles (e.g. rolling updates, Blue-Green layouts)."
    )
    ci_cd_pipeline: str = Field(
        ...,
        description="Configuration workflow specifications for GitHub Actions or other pipelines."
    )
    cloud_recommendations: str = Field(
        ...,
        description="Hosting providers, managed databases, and caching infrastructure recommendations."
    )
    observability: str = Field(
        ...,
        description="APM integrations, distributed tracing, and metrics instrumentation."
    )
    monitoring: str = Field(
        ...,
        description="System health checks, response metrics, and error rate alerting rules."
    )
    logging: str = Field(
        ...,
        description="Log format schema templates, aggregations, and rotators."
    )
    scalability: str = Field(
        ...,
        description="Autoscaling policies, horizontal/vertical thresholds, and CPU utilization parameters."
    )
    backup_strategy: str = Field(
        ...,
        description="Snapshot intervals, replication rules, and data retention schedules."
    )
    production_readiness: List[str] = Field(
        ...,
        description="Complete list of infrastructure checkpoints verifying readiness for deployment."
    )
