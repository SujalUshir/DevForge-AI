"""
Design Lead Agent implementation.

Generates UX specs and dashboard navigation wireframe flows.
"""

from typing import Dict, Any
import structlog

from agents.base import BaseAgent
from context.manager import ContextManager
from prompts.manager import PromptLoader
from shared_schemas import DesignLeadResponse

logger = structlog.get_logger(__name__)


class DesignLeadAgent(BaseAgent):
    """
    Design Lead Agent produces wireframe visual guides and navigation hierarchy specs.
    """

    @property
    def name(self) -> str:
        return "Design Lead"

    @property
    def department(self) -> str:
        return "Planning"

    async def _execute_task(self, context_manager: ContextManager) -> Dict[str, Any]:
        # 1. Load system prompt template
        loader = PromptLoader()
        system_prompt = loader.load_prompt("design_lead.md")

        # 2. Extract inputs from context
        metadata = context_manager.get_metadata()
        planning = context_manager.get_planning()
        project_name = metadata.get("project_name", "")
        user_idea = metadata.get("user_idea", "")
        prd_markdown = planning.get("prd_markdown", "")

        user_prompt = (
            f"Project Name: {project_name}\n"
            f"Product Idea: {user_idea}\n"
            f"Product Requirements Document (PRD):\n{prd_markdown}\n"
        )

        # 3. Call LLM Adapter
        logger.info("design_lead_invoking_llm", project_name=project_name)
        structured_response: DesignLeadResponse = await self.llm_adapter.generate_structured_output(
            system_instruction=system_prompt,
            prompt=user_prompt,
            response_schema=DesignLeadResponse,
            temperature=0.2
        )

        # 4. Update planning slice in Context
        logger.info("design_lead_updating_context", project_name=project_name)
        await context_manager.update_planning(
            self.name,
            lambda plan: setattr(plan, "ux_layout_specs", structured_response.ux_layout_specs)
        )

        return structured_response.model_dump()
