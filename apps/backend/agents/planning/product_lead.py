"""
Product Lead Agent implementation.

Generates the PRD based on refined project metadata.
"""

from typing import Dict, Any
import structlog

from agents.base import BaseAgent
from context.manager import ContextManager
from prompts.manager import PromptLoader
from shared_schemas import ProductLeadResponse

logger = structlog.get_logger(__name__)


class ProductLeadAgent(BaseAgent):
    """
    Product Lead Agent generates the functional PRD for the project.
    """

    @property
    def name(self) -> str:
        return "Product Lead"

    @property
    def department(self) -> str:
        return "Planning"

    async def _execute_task(self, context_manager: ContextManager) -> Dict[str, Any]:
        # 1. Load system prompt template
        loader = PromptLoader()
        system_prompt = loader.load_prompt("product_lead.md")

        # 2. Extract inputs from context
        metadata = context_manager.get_metadata()
        project_name = metadata.get("project_name", "")
        tech_stack = metadata.get("tech_stack", {})
        user_idea = metadata.get("user_idea", "")

        user_prompt = (
            f"Project Name: {project_name}\n"
            f"Product Idea: {user_idea}\n"
            f"Tech Stack:\n"
            f"- Frontend: {tech_stack.get('frontend')}\n"
            f"- Backend: {tech_stack.get('backend')}\n"
            f"- Database: {tech_stack.get('database')}\n"
        )

        # 3. Call LLM Adapter
        logger.info("product_lead_invoking_llm", project_name=project_name)
        structured_response: ProductLeadResponse = await self.llm_adapter.generate_structured_output(
            system_instruction=system_prompt,
            prompt=user_prompt,
            response_schema=ProductLeadResponse,
            temperature=0.2
        )

        # 4. Update planning slice in Context
        logger.info("product_lead_updating_context", project_name=project_name)
        
        def update_planning_context(plan):
            plan.prd_markdown = structured_response.prd_markdown

        await context_manager.update_planning(self.name, update_planning_context)

        return structured_response.model_dump()
