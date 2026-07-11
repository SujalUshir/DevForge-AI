"""
Frontend Lead Agent implementation.
"""

from typing import Dict, Any
import structlog

from agents.base import BaseAgent
from context.manager import ContextManager
from prompts.manager import PromptLoader
from shared_schemas import FrontendLeadResponse

logger = structlog.get_logger(__name__)


class FrontendLeadAgent(BaseAgent):
    """
    Frontend Lead Agent analyzes design layouts and system specifications to generate 
    frontend routing, state management, layouts, accessibility, and visual guidelines.
    """

    @property
    def name(self) -> str:
        return "Frontend Lead"

    @property
    def department(self) -> str:
        return "Engineering"

    async def _execute_task(self, context_manager: ContextManager) -> Dict[str, Any]:
        # 1. Load system prompt template
        loader = PromptLoader()
        system_prompt = loader.load_prompt("frontend_lead.md")

        # 2. Extract inputs from Context Manager
        metadata = context_manager.get_metadata()
        project_name = metadata.get("project_name", "")
        tech_stack = metadata.get("tech_stack", {})
        user_idea = metadata.get("user_idea", "")

        # Extract planning, architecture, and backend engineering context slices
        planning = context_manager.get_planning()
        prd_markdown = planning.get("prd_markdown", "")
        ux_layout_specs = planning.get("ux_layout_specs", "")

        architecture = context_manager.get_architecture()
        topology_markdown = architecture.get("topology_markdown", "")
        design_rationale = architecture.get("design_rationale", "")

        engineering = context_manager.get_engineering()
        api_spec_yaml = engineering.get("api_spec_yaml", "")

        user_prompt = (
            f"Project Name: {project_name}\n"
            f"Product Idea: {user_idea}\n"
            f"Tech Stack:\n"
            f"- Frontend: {tech_stack.get('frontend')}\n"
            f"- Backend: {tech_stack.get('backend')}\n"
            f"- Database: {tech_stack.get('database')}\n\n"
            f"--- Functional Specifications (PRD) ---\n"
            f"{prd_markdown}\n\n"
            f"--- UX Layout Specs ---\n"
            f"{ux_layout_specs}\n\n"
            f"--- System Topology (Mermaid) ---\n"
            f"{topology_markdown}\n\n"
            f"--- Architecture Design Rationale ---\n"
            f"{design_rationale}\n\n"
            f"--- Backend APIs Specs (OpenAPI) ---\n"
            f"{api_spec_yaml}\n"
        )

        # 3. Invoke LLM Adapter
        logger.info("frontend_lead_invoking_llm", project_name=project_name)
        structured_response: FrontendLeadResponse = await self.llm_adapter.generate_structured_output(
            system_instruction=system_prompt,
            prompt=user_prompt,
            response_schema=FrontendLeadResponse,
            temperature=0.2
        )

        # 4. Save to Context Manager
        logger.info("frontend_lead_updating_context", project_name=project_name)
        
        def update_engineering_context(eng):
            eng.frontend_architecture = structured_response.frontend_architecture
            eng.frontend_pages = structured_response.frontend_pages
            eng.components = structured_response.components
            eng.layout = structured_response.layout
            eng.routing = structured_response.routing
            eng.state_management = structured_response.state_management
            eng.styling_approach = structured_response.styling_approach
            eng.accessibility_checklist = structured_response.accessibility_checklist
            eng.responsive_design = structured_response.responsive_design
            eng.folder_structure_frontend = structured_response.folder_structure

        await context_manager.update_engineering(self.name, update_engineering_context)

        return structured_response.model_dump()
