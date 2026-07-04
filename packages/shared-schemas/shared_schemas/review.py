"""
Pydantic schemas for the Review Department agents.
"""

from pydantic import BaseModel, Field
from typing import List


class EngineeringDirectorResponse(BaseModel):
    """
    Structured JSON output schema for Engineering Director Agent.
    """
    approved: bool = Field(
        ...,
        description="Gate approval decision. True if no critical issues exist, otherwise False."
    )
    overall_score: float = Field(
        ...,
        description="Overall technical review quality score between 0.0 and 10.0."
    )
    critical_issues: List[str] = Field(
        ...,
        description="List of blocking errors (missing major features, incorrect API designs)."
    )
    major_issues: List[str] = Field(
        ...,
        description="List of important recommendations (security additions, database optimizations)."
    )
    minor_issues: List[str] = Field(
        ...,
        description="List of small fixes, formatting issues, or lint recommendations."
    )
    missing_sections: List[str] = Field(
        ...,
        description="List of required specs or fields that were left empty."
    )
    architecture_review: str = Field(
        ...,
        description="Review comments focusing on system topology and design choices."
    )
    engineering_review: str = Field(
        ...,
        description="Review comments focusing on database SQL specs and API OpenAPI layouts."
    )
    security_review: str = Field(
        ...,
        description="Review comments focusing on auth flow controls and threat models."
    )
    quality_review: str = Field(
        ...,
        description="Review comments focusing on testing plans and container pipelines."
    )
    final_recommendations: str = Field(
        ...,
        description="Advice for subsequent steps or actionable correction directives."
    )
    approval_summary: str = Field(
        ...,
        description="Summary explaining the final gate status decision."
    )
