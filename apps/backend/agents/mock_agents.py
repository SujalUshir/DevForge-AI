"""
Mock Agent implementations representing the 11 company specialist roles.
These agents simulate updates to the SharedProjectContext in a structured manner.
"""

from typing import Dict, Any
from agents.base import BaseAgent
from context.manager import ContextManager


# ── PLANNING DEPARTMENT ──────────────────────────────────────────────────────

class MockProductLead(BaseAgent):
    @property
    def name(self) -> str:
        return "Product Lead"

    @property
    def department(self) -> str:
        return "Planning"

    async def _execute_task(self, context_manager: ContextManager) -> Dict[str, Any]:
        # Product Lead produces PRD markdown
        prd_content = (
            "# Product Requirements Document (PRD)\n\n"
            "## MVP Scope\n"
            "- User registration and secure login session tokens.\n"
            "- Real-time progress notifications."
        )
        # Enforce lock and write to context
        await context_manager.update_planning(
            self.name,
            lambda plan: setattr(plan, "prd_markdown", prd_content)
        )
        return {"prd_markdown": prd_content}


class MockMarketAnalyst(BaseAgent):
    @property
    def name(self) -> str:
        return "Market Analyst"

    @property
    def department(self) -> str:
        return "Planning"

    async def _execute_task(self, context_manager: ContextManager) -> Dict[str, Any]:
        brief = (
            "# Competitor Analysis Brief\n\n"
            "## SWOT\n"
            "- Strengths: Multi-agent execution pipelines.\n"
            "- Weaknesses: Dependency on LLM speed limits."
        )
        await context_manager.update_planning(
            self.name,
            lambda plan: setattr(plan, "competitor_brief_markdown", brief)
        )
        return {"competitor_brief_markdown": brief}


class MockDesignLead(BaseAgent):
    @property
    def name(self) -> str:
        return "Design Lead"

    @property
    def department(self) -> str:
        return "Planning"

    async def _execute_task(self, context_manager: ContextManager) -> Dict[str, Any]:
        specs = (
            "## Wireframe Layout Specs\n"
            "- Workspace: Side drawer for logs, central pane for blueprints.\n"
            "- Landing: Clean grid structure, hero with dynamic neon colors."
        )
        await context_manager.update_planning(
            self.name,
            lambda plan: setattr(plan, "ux_layout_specs", specs)
        )
        return {"ux_layout_specs": specs}


# ── ARCHITECTURE DEPARTMENT ──────────────────────────────────────────────────

class MockPrincipalArchitect(BaseAgent):
    @property
    def name(self) -> str:
        return "Principal Architect"

    @property
    def department(self) -> str:
        return "Architecture"

    async def _execute_task(self, context_manager: ContextManager) -> Dict[str, Any]:
        topology = (
            "# System Architecture Topology\n\n"
            "```mermaid\n"
            "graph TD\n"
            "  Client --> Gateway --> FastAPI\n"
            "```"
        )
        rationale = "Decoupled mock execution layer for testability."
        
        await context_manager.update_architecture(
            self.name,
            lambda arch: [
                setattr(arch, "topology_markdown", topology),
                setattr(arch, "design_rationale", rationale)
            ]
        )
        return {"topology_markdown": topology, "design_rationale": rationale}


# ── ENGINEERING DEPARTMENT ───────────────────────────────────────────────────

class MockBackendLead(BaseAgent):
    @property
    def name(self) -> str:
        return "Backend Lead"

    @property
    def department(self) -> str:
        return "Engineering"

    async def _execute_task(self, context_manager: ContextManager) -> Dict[str, Any]:
        api_spec = (
            "openapi: 3.0.0\n"
            "info:\n"
            "  title: DevForge Application APIs\n"
            "  version: 1.0.0"
        )
        db_schema = (
            "CREATE TABLE users (\n"
            "  id UUID PRIMARY KEY,\n"
            "  name VARCHAR(100)\n"
            ");"
        )
        backend_main = (
            "from fastapi import FastAPI\n"
            "app = FastAPI()\n"
        )
        
        await context_manager.update_engineering(
            self.name,
            lambda eng: [
                setattr(eng, "api_spec_yaml", api_spec),
                setattr(eng, "database_schema_sql", db_schema),
                setattr(eng, "backend_main_py", backend_main)
            ]
        )
        return {
            "api_spec_yaml": api_spec,
            "database_schema_sql": db_schema,
            "backend_main_py": backend_main
        }


class MockFrontendLead(BaseAgent):
    @property
    def name(self) -> str:
        return "Frontend Lead"

    @property
    def department(self) -> str:
        return "Engineering"

    async def _execute_task(self, context_manager: ContextManager) -> Dict[str, Any]:
        # Frontend Lead contributes to structural logs and directory blueprints
        # Return mock routes configuration
        return {"routes_scaffold": "apps/frontend/pages/index.tsx"}


# ── VALIDATION DEPARTMENT ────────────────────────────────────────────────────

class MockSecurityLead(BaseAgent):
    @property
    def name(self) -> str:
        return "Security Lead"

    @property
    def department(self) -> str:
        return "Validation"

    async def _execute_task(self, context_manager: ContextManager) -> Dict[str, Any]:
        report = (
            "# Threat Modeling Security Report\n"
            "- Rate limiting on open routes to prevent DDoS.\n"
            "- Env variables sanitized to filter API keys."
        )
        await context_manager.update_validation(
            self.name,
            lambda val: setattr(val, "security_report_markdown", report)
        )
        return {"security_report_markdown": report}


class MockQALead(BaseAgent):
    @property
    def name(self) -> str:
        return "QA Lead"

    @property
    def department(self) -> str:
        return "Validation"

    async def _execute_task(self, context_manager: ContextManager) -> Dict[str, Any]:
        plan = (
            "# Integration and QA Test Plan\n"
            "- Mock context serialization validation suite.\n"
            "- Health check API uptime monitors."
        )
        await context_manager.update_validation(
            self.name,
            lambda val: setattr(val, "test_plan_markdown", plan)
        )
        return {"test_plan_markdown": plan}


class MockPlatformEngineer(BaseAgent):
    @property
    def name(self) -> str:
        return "Platform Engineer"

    @property
    def department(self) -> str:
        return "Validation"

    async def _execute_task(self, context_manager: ContextManager) -> Dict[str, Any]:
        # Target internal Pydantic DevOpsConfigs model fields
        dockerfile = "FROM python:3.11-slim\n"
        compose = "version: '3.8'\nservices:\n  web:\n"
        
        def update_devops(val_slice):
            val_slice.devops_configs.dockerfile = dockerfile
            val_slice.devops_configs.docker_compose_yml = compose

        await context_manager.update_validation(self.name, update_devops)
        return {"dockerfile": dockerfile, "docker_compose_yml": compose}


# ── REVIEW DEPARTMENT ────────────────────────────────────────────────────────

class MockEngineeringDirector(BaseAgent):
    def __init__(self, force_reject_once: bool = False):
        super().__init__()
        self.force_reject_once = force_reject_once
        self._rejections = 0

    @property
    def name(self) -> str:
        return "Engineering Director"

    @property
    def department(self) -> str:
        return "Review"

    async def _execute_task(self, context_manager: ContextManager) -> Dict[str, Any]:
        if self.force_reject_once and self._rejections == 0:
            self._rejections += 1
            feedback = ["Missing rate limiting check in backend_main_py configuration."]
            await context_manager.update_review(
                self.name,
                lambda rev: [
                    setattr(rev, "approved", False),
                    setattr(rev, "reviewer_feedback", feedback)
                ]
            )
            return {"approved": False, "reviewer_feedback": feedback}
            
        # Standard flow: approve
        await context_manager.update_review(
            self.name,
            lambda rev: [
                setattr(rev, "approved", True),
                setattr(rev, "reviewer_feedback", [])
            ]
        )
        return {"approved": True, "reviewer_feedback": []}
