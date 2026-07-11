"""
QA Lead Agent implementation.
"""

from typing import Dict, Any
import structlog

from agents.base import BaseAgent
from context.manager import ContextManager
from prompts.manager import PromptLoader
from shared_schemas import QALeadResponse

logger = structlog.get_logger(__name__)


class QALeadAgent(BaseAgent):
    """
    QA Lead Agent analyzes requirements, architecture and specifications to formulate 
    unit, integration, API, and E2E testing strategies, edge cases and checklists.
    """

    @property
    def name(self) -> str:
        return "QA Lead"

    @property
    def department(self) -> str:
        return "Validation"

    async def _execute_task(self, context_manager: ContextManager) -> Dict[str, Any]:
        # 1. Load system prompt template
        loader = PromptLoader()
        system_prompt = loader.load_prompt("qa_lead.md")

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
            f"{api_spec_yaml}\n"
        )

        # 3. Invoke LLM Adapter
        logger.info("qa_lead_invoking_llm", project_name=project_name)
        structured_response: QALeadResponse = await self.llm_adapter.generate_structured_output(
            system_instruction=system_prompt,
            prompt=user_prompt,
            response_schema=QALeadResponse,
            temperature=0.2
        )

        # 4. Save to Context Manager
        logger.info("qa_lead_updating_context", project_name=project_name)
        
        def update_validation_context(val):
            val.test_plan_markdown = structured_response.test_plan_markdown
            val.unit_testing_strategy = structured_response.unit_testing_strategy
            val.integration_tests = structured_response.integration_tests
            val.api_tests = structured_response.api_tests
            val.frontend_testing = structured_response.frontend_testing
            val.edge_cases = structured_response.edge_cases
            val.acceptance_criteria = structured_response.acceptance_criteria
            val.regression_testing = structured_response.regression_testing
            val.manual_testing_checklist = structured_response.manual_testing_checklist
            val.quality_risks = structured_response.quality_risks

        await context_manager.update_validation(self.name, update_validation_context)

        return structured_response.model_dump()
