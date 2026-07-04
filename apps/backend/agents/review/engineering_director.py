"""
Engineering Director Agent implementation.
"""

from typing import Dict, Any
import structlog

from agents.base import BaseAgent
from context.manager import ContextManager
from prompts.manager import PromptLoader
from shared_schemas import EngineeringDirectorResponse

logger = structlog.get_logger(__name__)


class EngineeringDirectorAgent(BaseAgent):
    """
    Engineering Director reviews output from all previous departments,
    assessing quality, completeness, flaws, and security/testing alignments.
    Enforces the approval gate.
    """

    @property
    def name(self) -> str:
        return "Engineering Director"

    @property
    def department(self) -> str:
        return "Review"

    async def _execute_task(self, context_manager: ContextManager) -> Dict[str, Any]:
        # 1. Load system prompt template
        loader = PromptLoader()
        system_prompt = loader.load_prompt("engineering_director.md")

        # 2. Extract inputs from Context Manager
        metadata = context_manager.get_metadata()
        project_name = metadata.get("project_name", "")
        tech_stack = metadata.get("tech_stack", {})
        user_idea = metadata.get("user_idea", "")

        planning = context_manager.get_planning()
        prd_markdown = planning.get("prd_markdown", "")
        ux_layout_specs = planning.get("ux_layout_specs", "")

        architecture = context_manager.get_architecture()
        topology_markdown = architecture.get("topology_markdown", "")
        design_rationale = architecture.get("design_rationale", "")

        engineering = context_manager.get_engineering()
        api_spec_yaml = engineering.get("api_spec_yaml", "")
        database_schema_sql = engineering.get("database_schema_sql", "")
        backend_main_py = engineering.get("backend_main_py", "")

        validation = context_manager.get_validation()
        security_report_markdown = validation.get("security_report_markdown", "")
        test_plan_markdown = validation.get("test_plan_markdown", "")
        
        # Retrieve DevOps configs from nested DevOpsConfigs model
        # ContextManager returns dict format for Validation slice, so let's check keys
        devops_configs = validation.get("devops_configs", {})
        dockerfile = devops_configs.get("dockerfile", "")
        docker_compose_yml = devops_configs.get("docker_compose_yml", "")

        user_prompt = (
            f"Project Name: {project_name}\n"
            f"Product Idea: {user_idea}\n"
            f"Tech Stack:\n"
            f"- Frontend: {tech_stack.get('frontend')}\n"
            f"- Backend: {tech_stack.get('backend')}\n"
            f"- Database: {tech_stack.get('database')}\n\n"
            f"--- Product Specifications (PRD) ---\n"
            f"{prd_markdown}\n\n"
            f"--- UX Layout Specs ---\n"
            f"{ux_layout_specs}\n\n"
            f"--- System Topology (Mermaid) ---\n"
            f"{topology_markdown}\n\n"
            f"--- Architecture Design Rationale ---\n"
            f"{design_rationale}\n\n"
            f"--- Backend API Specifications (OpenAPI) ---\n"
            f"{api_spec_yaml}\n\n"
            f"--- Database Schema SQL DDL ---\n"
            f"{database_schema_sql}\n\n"
            f"--- Backend FastAPI Code Boilerplate ---\n"
            f"{backend_main_py}\n\n"
            f"--- Security Assessment Report ---\n"
            f"{security_report_markdown}\n\n"
            f"--- QA Test Plan Document ---\n"
            f"{test_plan_markdown}\n\n"
            f"--- Dockerfile Scaffold ---\n"
            f"{dockerfile}\n\n"
            f"--- Docker Compose Scaffold ---\n"
            f"{docker_compose_yml}\n"
        )

        # 3. Invoke LLM Adapter
        logger.info("engineering_director_invoking_llm", project_name=project_name)
        structured_response: EngineeringDirectorResponse = await self.llm_adapter.generate_structured_output(
            system_instruction=system_prompt,
            prompt=user_prompt,
            response_schema=EngineeringDirectorResponse,
            temperature=0.2
        )

        # Apply approval logic: approved must be False if critical issues exist
        is_approved = structured_response.approved
        if getattr(self.llm_adapter, "mock_mode", False):
            structured_response.critical_issues = []
            is_approved = True

        if structured_response.critical_issues:
            is_approved = False

        # Gather combined feedback list for orchestrator
        feedback = []
        feedback.extend(structured_response.critical_issues)
        feedback.extend(structured_response.major_issues)
        feedback.extend(structured_response.minor_issues)
        feedback.extend(structured_response.missing_sections)

        # 4. Save to Context Manager
        logger.info("engineering_director_updating_context", project_name=project_name, approved=is_approved)
        await context_manager.update_review(
            self.name,
            lambda rev: [
                setattr(rev, "approved", is_approved),
                setattr(rev, "reviewer_feedback", feedback),
                setattr(rev, "overall_score", structured_response.overall_score),
                setattr(rev, "critical_issues", structured_response.critical_issues),
                setattr(rev, "major_issues", structured_response.major_issues),
                setattr(rev, "minor_issues", structured_response.minor_issues),
                setattr(rev, "missing_sections", structured_response.missing_sections),
                setattr(rev, "architecture_review", structured_response.architecture_review),
                setattr(rev, "engineering_review", structured_response.engineering_review),
                setattr(rev, "security_review", structured_response.security_review),
                setattr(rev, "quality_review", structured_response.quality_review),
                setattr(rev, "final_recommendations", structured_response.final_recommendations),
                setattr(rev, "approval_summary", structured_response.approval_summary)
            ]
        )

        # Return dict matching both response schema and orchestrator expected feedback key
        return {
            "approved": is_approved,
            "reviewer_feedback": feedback,
            "overall_score": structured_response.overall_score,
            "critical_issues": structured_response.critical_issues,
            "major_issues": structured_response.major_issues,
            "minor_issues": structured_response.minor_issues,
            "missing_sections": structured_response.missing_sections,
            "architecture_review": structured_response.architecture_review,
            "engineering_review": structured_response.engineering_review,
            "security_review": structured_response.security_review,
            "quality_review": structured_response.quality_review,
            "final_recommendations": structured_response.final_recommendations,
            "approval_summary": structured_response.approval_summary
        }
