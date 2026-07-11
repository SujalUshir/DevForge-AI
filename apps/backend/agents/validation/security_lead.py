"""
Security Lead Agent implementation.
"""

from typing import Dict, Any
import structlog

from agents.base import BaseAgent
from context.manager import ContextManager
from prompts.manager import PromptLoader
from shared_schemas import SecurityLeadResponse

logger = structlog.get_logger(__name__)


class SecurityLeadAgent(BaseAgent):
    """
    Security Lead Agent analyzes requirements, architecture, and backend blueprints
    to formulate threat models, OWASP checklists, input validation, and rate limits.
    """

    @property
    def name(self) -> str:
        return "Security Lead"

    @property
    def department(self) -> str:
        return "Validation"

    async def _execute_task(self, context_manager: ContextManager) -> Dict[str, Any]:
        # 1. Load system prompt template
        loader = PromptLoader()
        system_prompt = loader.load_prompt("security_lead.md")

        # 2. Extract inputs from Context Manager
        metadata = context_manager.get_metadata()
        project_name = metadata.get("project_name", "")
        tech_stack = metadata.get("tech_stack", {})
        user_idea = metadata.get("user_idea", "")

        planning = context_manager.get_planning()
        prd_markdown = planning.get("prd_markdown", "")

        architecture = context_manager.get_architecture()
        topology_markdown = architecture.get("topology_markdown", "")

        engineering = context_manager.get_engineering()
        api_spec_yaml = engineering.get("api_spec_yaml", "")
        database_schema_sql = engineering.get("database_schema_sql", "")

        user_prompt = (
            f"Project Name: {project_name}\n"
            f"Product Idea: {user_idea}\n"
            f"Tech Stack:\n"
            f"- Frontend: {tech_stack.get('frontend')}\n"
            f"- Backend: {tech_stack.get('backend')}\n"
            f"- Database: {tech_stack.get('database')}\n\n"
            f"--- Product Specifications (PRD) ---\n"
            f"{prd_markdown}\n\n"
            f"--- System Topology (Mermaid) ---\n"
            f"{topology_markdown}\n\n"
            f"--- Backend API Specifications (OpenAPI) ---\n"
            f"{api_spec_yaml}\n\n"
            f"--- Database Schema SQL DDL ---\n"
            f"{database_schema_sql}\n"
        )

        # 3. Invoke LLM Adapter
        logger.info("security_lead_invoking_llm", project_name=project_name)
        structured_response: SecurityLeadResponse = await self.llm_adapter.generate_structured_output(
            system_instruction=system_prompt,
            prompt=user_prompt,
            response_schema=SecurityLeadResponse,
            temperature=0.2
        )

        # 4. Save to Context Manager
        logger.info("security_lead_updating_context", project_name=project_name)
        
        def update_validation_context(val):
            val.security_report_markdown = structured_response.security_report_markdown
            val.auth_recommendations = structured_response.auth_recommendations
            val.authorization_strategy = structured_response.authorization_strategy
            val.secret_management = structured_response.secret_management
            val.owasp_checklist = structured_response.owasp_checklist
            val.api_security = structured_response.api_security
            val.input_validation = structured_response.input_validation
            val.rate_limiting = structured_response.rate_limiting
            val.encryption_recommendations = structured_response.encryption_recommendations
            val.dependency_risks = structured_response.dependency_risks
            val.production_security_checklist = structured_response.production_checklist

        await context_manager.update_validation(self.name, update_validation_context)

        return structured_response.model_dump()
