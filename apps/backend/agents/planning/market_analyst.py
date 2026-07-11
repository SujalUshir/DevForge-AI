"""
Market Analyst Agent implementation.

Generates SWOT and competitor brief analysis.
"""

from typing import Dict, Any
import structlog

from agents.base import BaseAgent
from context.manager import ContextManager
from prompts.manager import PromptLoader
from shared_schemas import MarketAnalystResponse

logger = structlog.get_logger(__name__)


class MarketAnalystAgent(BaseAgent):
    """
    Market Analyst Agent reviews competitive fields and SWOT indicators.
    """

    @property
    def name(self) -> str:
        return "Market Analyst"

    @property
    def department(self) -> str:
        return "Planning"

    async def _execute_task(self, context_manager: ContextManager) -> Dict[str, Any]:
        # 1. Load system prompt template
        loader = PromptLoader()
        system_prompt = loader.load_prompt("market_analyst.md")

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
        logger.info("market_analyst_invoking_llm", project_name=project_name)
        structured_response: MarketAnalystResponse = await self.llm_adapter.generate_structured_output(
            system_instruction=system_prompt,
            prompt=user_prompt,
            response_schema=MarketAnalystResponse,
            temperature=0.4
        )

        # 4. Update planning slice in Context
        logger.info("market_analyst_updating_context", project_name=project_name)
        
        def update_planning_context(plan):
            plan.competitor_brief_markdown = structured_response.competitor_brief_markdown

        await context_manager.update_planning(self.name, update_planning_context)

        return structured_response.model_dump()
