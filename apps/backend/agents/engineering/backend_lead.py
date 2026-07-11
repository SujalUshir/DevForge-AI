"""
Backend Lead Agent implementation.
"""

from typing import Dict, Any
import structlog

from agents.base import BaseAgent
from context.manager import ContextManager
from prompts.manager import PromptLoader
from shared_schemas import BackendLeadResponse

logger = structlog.get_logger(__name__)


class BackendLeadAgent(BaseAgent):
    """
    Backend Lead Agent analyzes requirements and system architecture to generate 
    database DDL, API OpenAPI specs, FastAPI boilerplate, and backend structure.
    """

    @property
    def name(self) -> str:
        return "Backend Lead"

    @property
    def department(self) -> str:
        return "Engineering"

    async def _execute_task(self, context_manager: ContextManager) -> Dict[str, Any]:
        # 1. Load system prompt template
        loader = PromptLoader()
        system_prompt = loader.load_prompt("backend_lead.md")

        # 2. Extract inputs from Context Manager
        metadata = context_manager.get_metadata()
        project_name = metadata.get("project_name", "")
        tech_stack = metadata.get("tech_stack", {})
        user_idea = metadata.get("user_idea", "")

        # Extract planning & architecture references
        planning = context_manager.get_planning()
        prd_markdown = planning.get("prd_markdown", "")
        ux_layout_specs = planning.get("ux_layout_specs", "")

        architecture = context_manager.get_architecture()
        topology_markdown = architecture.get("topology_markdown", "")
        design_rationale = architecture.get("design_rationale", "")

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
            f"{design_rationale}\n"
        )

        # 3. Invoke LLM Adapter
        logger.info("backend_lead_invoking_llm", project_name=project_name)
        structured_response: BackendLeadResponse = await self.llm_adapter.generate_structured_output(
            system_instruction=system_prompt,
            prompt=user_prompt,
            response_schema=BackendLeadResponse,
            temperature=0.2
        )

        # 4. Save to Context Manager
        logger.info("backend_lead_updating_context", project_name=project_name)
        
        def update_engineering_context(eng):
            eng.api_spec_yaml = structured_response.api_spec_yaml
            eng.database_schema_sql = structured_response.database_schema_sql
            eng.backend_main_py = structured_response.backend_main_py
            eng.backend_architecture = structured_response.backend_architecture
            eng.backend_services = structured_response.backend_services
            eng.api_design = structured_response.api_design
            eng.database_notes = structured_response.database_notes
            eng.folder_structure_backend = structured_response.folder_structure
            eng.security_notes = structured_response.security_notes

        await context_manager.update_engineering(self.name, update_engineering_context)

        return structured_response.model_dump()
