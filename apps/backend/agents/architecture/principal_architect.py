"""
Principal Architect Agent implementation.

Generates system topology and design rationale.
"""

from typing import Dict, Any
import structlog

from agents.base import BaseAgent
from context.manager import ContextManager
from prompts.manager import PromptLoader
from shared_schemas import PrincipalArchitectResponse

logger = structlog.get_logger(__name__)


class PrincipalArchitectAgent(BaseAgent):
    """
    Principal Architect Agent models system structure blueprints.
    """

    @property
    def name(self) -> str:
        return "Principal Architect"

    @property
    def department(self) -> str:
        return "Architecture"

    async def _execute_task(self, context_manager: ContextManager) -> Dict[str, Any]:
        # 1. Load system prompt template
        loader = PromptLoader()
        system_prompt = loader.load_prompt("principal_architect.md")

        # 2. Extract inputs from context
        metadata = context_manager.get_metadata()
        planning = context_manager.get_planning()
        
        project_name = metadata.get("project_name", "")
        user_idea = metadata.get("user_idea", "")
        prd_markdown = planning.get("prd_markdown", "")
        ux_layout_specs = planning.get("ux_layout_specs", "")

        user_prompt = (
            f"Project Name: {project_name}\n"
            f"Product Idea: {user_idea}\n"
            f"Product Requirements Document (PRD):\n{prd_markdown}\n"
            f"UX Layout Specifications:\n{ux_layout_specs}\n"
        )

        # 3. Call LLM Adapter
        logger.info("principal_architect_invoking_llm", project_name=project_name)
        structured_response: PrincipalArchitectResponse = await self.llm_adapter.generate_structured_output(
            system_instruction=system_prompt,
            prompt=user_prompt,
            response_schema=PrincipalArchitectResponse,
            temperature=0.2
        )

        # 4. Update architecture slice in Context
        logger.info("principal_architect_updating_context", project_name=project_name)
        await context_manager.update_architecture(
            self.name,
            lambda arch: [
                setattr(arch, "topology_markdown", structured_response.topology_markdown),
                setattr(arch, "design_rationale", structured_response.design_rationale)
            ]
        )

        return structured_response.model_dump()
