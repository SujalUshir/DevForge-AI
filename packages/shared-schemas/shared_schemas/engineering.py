"""
Pydantic schemas for the Engineering Department agents.
"""

from pydantic import BaseModel, Field
from typing import List


class BackendLeadResponse(BaseModel):
    """
    Structured JSON output schema for Backend Lead Agent.
    """
    backend_architecture: str = Field(
        ...,
        description="High-level overview of backend services, APIs, and micro-architecture."
    )
    backend_services: List[str] = Field(
        ...,
        description="Core background services, controllers, and workers needed."
    )
    api_design: str = Field(
        ...,
        description="API endpoint architecture, controller schemas, and REST request/response mapping."
    )
    api_spec_yaml: str = Field(
        ...,
        description="Valid OpenAPI 3.0 specification in clean YAML format representing the API endpoints."
    )
    database_schema_sql: str = Field(
        ...,
        description="DDL schema scripts including tables, columns, indexes, and primary/foreign keys in clean SQL format."
    )
    backend_main_py: str = Field(
        ...,
        description="FastAPI main application entrypoint skeleton code in clean Python format."
    )
    database_notes: str = Field(
        ...,
        description="Database indexing, design decisions, and optimizations."
    )
    folder_structure: str = Field(
        ...,
        description="Text map representing the backend workspace directory structure layout."
    )
    security_notes: str = Field(
        ...,
        description="Security mechanisms, JWT session details, and access control scopes."
    )
    dependencies: List[str] = Field(
        ...,
        description="Recommended third-party libraries and packages needed for backend."
    )


class FrontendLeadResponse(BaseModel):
    """
    Structured JSON output schema for Frontend Lead Agent.
    """
    frontend_architecture: str = Field(
        ...,
        description="High-level frontend architecture, rendering models, and state management pattern."
    )
    frontend_pages: List[str] = Field(
        ...,
        description="Page hierarchy list with descriptions, routing scopes, and layout assignments."
    )
    routing: str = Field(
        ...,
        description="Frontend router details, page endpoints, middleware configurations."
    )
    components: List[str] = Field(
        ...,
        description="Reusable UI layout components, styles configurations, and parameters."
    )
    layout: str = Field(
        ...,
        description="Design system tree, grid/spacing details, and component hierarchy specifications."
    )
    state_management: str = Field(
        ...,
        description="Details on client-side state managers, hooks, contexts, and actions."
    )
    styling_approach: str = Field(
        ...,
        description="CSS structure, themes, styling patterns, and visual parameters."
    )
    accessibility_checklist: List[str] = Field(
        ...,
        description="Strict checklist complying with WCAG requirements for interactive layouts."
    )
    responsive_design: str = Field(
        ...,
        description="Visual viewport breakpoints, layout flexibilities, and scaling rules."
    )
    folder_structure: str = Field(
        ...,
        description="Text map representing the frontend workspace directory structure layout."
    )
