"""
Pydantic schemas for the Planning Department agents.
"""

from pydantic import BaseModel, Field


class ProductLeadResponse(BaseModel):
    """
    Structured JSON output schema for Product Lead Agent.
    """
    prd_markdown: str = Field(
        ...,
        description="The finalized Product Requirements Document (PRD) content in clean Markdown format."
    )


class MarketAnalystResponse(BaseModel):
    """
    Structured JSON output schema for Market Analyst Agent.
    """
    competitor_brief_markdown: str = Field(
        ...,
        description="SWOT analysis, market trends, and competitor profiles in clean Markdown format."
    )


class DesignLeadResponse(BaseModel):
    """
    Structured JSON output schema for Design Lead Agent.
    """
    ux_layout_specs: str = Field(
        ...,
        description="UX navigation hierarchy, visual components list, and dashboard layout specs in clean Markdown format."
    )
