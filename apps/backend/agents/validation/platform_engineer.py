"""
Platform Engineer Agent implementation.
"""

from typing import Dict, Any
import structlog

from agents.base import BaseAgent
from context.manager import ContextManager
from prompts.manager import PromptLoader
from shared_schemas import PlatformEngineerResponse

logger = structlog.get_logger(__name__)


class PlatformEngineerAgent(BaseAgent):
    """
    Platform Engineer Agent analyzes system blueprints and requirements to construct
    Docker configurations, deployment strategies, scaling configs, and observability parameters.
    """

    @property
    def name(self) -> str:
        return "Platform Engineer"

    @property
    def department(self) -> str:
        return "Validation"

    async def _execute_task(self, context_manager: ContextManager) -> Dict[str, Any]:
        # 1. Load system prompt template
        loader = PromptLoader()
        system_prompt = loader.load_prompt("platform_engineer.md")

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
        logger.info("platform_engineer_invoking_llm", project_name=project_name)
        structured_response: PlatformEngineerResponse = await self.llm_adapter.generate_structured_output(
            system_instruction=system_prompt,
            prompt=user_prompt,
            response_schema=PlatformEngineerResponse,
            temperature=0.2
        )

        # 4. Save to Context Manager
        logger.info("platform_engineer_updating_context", project_name=project_name)
        
        def update_validation_context(val):
            # Platform Engineer contributes to both root fields (dockerfile, docker_compose_yml inside devops_configs)
            # and custom attributes in validation context.
            val.devops_configs.dockerfile = structured_response.dockerfile
            val.devops_configs.docker_compose_yml = structured_response.docker_compose_yml
            val.deployment_strategy = structured_response.deployment_strategy
            val.ci_cd_pipeline = structured_response.ci_cd_pipeline
            val.cloud_recommendations = structured_response.cloud_recommendations
            val.observability = structured_response.observability
            val.monitoring = structured_response.monitoring
            val.logging = structured_response.logging
            val.scalability = structured_response.scalability
            val.backup_strategy = structured_response.backup_strategy
            val.production_readiness = structured_response.production_readiness

        await context_manager.update_validation(self.name, update_validation_context)

        return structured_response.model_dump()
