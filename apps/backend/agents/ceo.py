"""
CEO Agent implementation.

Analyzes raw user input ideas, refines project name, suggests tech stack
recommendations, and sets up the roadmap framework.
"""

from typing import Dict, List, Any
from pydantic import BaseModel, Field
import structlog

from agents.base import BaseAgent
from agents.models import AgentResponse
from context.manager import ContextManager
from prompts.manager import PromptLoader

logger = structlog.get_logger(__name__)


class CEOResponseSchema(BaseModel):
    """
    Strict output JSON schema for the CEO Agent.
    """
    refined_project_name: str = Field(..., description="A clean, startup-ready version of the project name.")
    project_vision: str = Field(..., description="High-level product vision statement and core value proposition.")
    suggested_frontend_stack: str = Field(..., description="Specific frontend framework selection (e.g. Next.js + Tailwind).")
    suggested_backend_stack: str = Field(..., description="Specific backend framework selection (e.g. FastAPI).")
    suggested_database_stack: str = Field(..., description="Specific database selection (e.g. PostgreSQL).")
    initial_milestones: List[str] = Field(..., description="A sequence of execution milestones for the multi-agent system.")


class CEOAgent(BaseAgent):
    """
    The CEO Agent bootstraps the forge sequence by analyzing raw user idea parameters.
    """

    @property
    def name(self) -> str:
        return "CEO Agent"

    @property
    def department(self) -> str:
        return "Management"

    async def _execute_task(self, context_manager: ContextManager) -> Dict[str, Any]:
        # 1. Load prompts using PromptLoader
        loader = PromptLoader()
        system_prompt = loader.load_prompt("ceo.md")

        # 2. Extract user input details from Shared Project Context
        metadata = context_manager.get_metadata()
        user_idea = metadata.get("user_idea", "")
        project_name = metadata.get("project_name", "")
        tech_stack = metadata.get("tech_stack", {})

        user_prompt = (
            f"Project Name Idea: {project_name}\n"
            f"User Idea Description: {user_idea}\n"
            f"Selected Stacks:\n"
            f"- Frontend: {tech_stack.get('frontend')}\n"
            f"- Backend: {tech_stack.get('backend')}\n"
            f"- Database: {tech_stack.get('database')}\n"
        )

        # 3. Call LLM Adapter for structured schema output
        logger.info("ceo_agent_invoking_llm", project_name=project_name)
        structured_response: CEOResponseSchema = await self.llm_adapter.generate_structured_output(
            system_instruction=system_prompt,
            prompt=user_prompt,
            response_schema=CEOResponseSchema,
            temperature=0.3
        )

        # 4. Update the Shared Project Context metadata slice under lock
        logger.info("ceo_agent_updating_context", refined_name=structured_response.refined_project_name)
        
        def update_metadata_slice(meta):
            meta.project_name = structured_response.refined_project_name
            meta.tech_stack.frontend = structured_response.suggested_frontend_stack
            meta.tech_stack.backend = structured_response.suggested_backend_stack
            meta.tech_stack.database = structured_response.suggested_database_stack

        await context_manager.update_metadata(self.name, update_metadata_slice)

        # ── Proof of Work: CEO Agent writes README.md via Filesystem MCP client ──
        try:
            logger.info("ceo_agent_mcp_readme_start")
            from mcp.filesystem import FilesystemMCPClient
            
            workspace_dir = None
            if hasattr(context_manager, "_persist_path") and context_manager._persist_path:
                workspace_dir = context_manager._persist_path.parent
            
            mcp_client = FilesystemMCPClient(workspace_root=workspace_dir, read_only=False)
            await mcp_client.connect()
            try:
                readme_content = (
                    f"# {structured_response.refined_project_name}\n\n"
                    f"## Vision\n{structured_response.project_vision}\n\n"
                    f"## Tech Stack\n"
                    f"- Frontend: {structured_response.suggested_frontend_stack}\n"
                    f"- Backend: {structured_response.suggested_backend_stack}\n"
                    f"- Database: {structured_response.suggested_database_stack}\n"
                )
                await mcp_client.write_file("README.md", readme_content)
                logger.info("ceo_agent_mcp_readme_success", path="README.md")
            finally:
                await mcp_client.disconnect()
        except Exception as exc:
            logger.error("ceo_agent_mcp_readme_failed", error=str(exc))

        return structured_response.model_dump()
