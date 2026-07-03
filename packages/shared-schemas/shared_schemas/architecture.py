"""
Pydantic schemas for the Architecture Department agents.
"""

from pydantic import BaseModel, Field


class PrincipalArchitectResponse(BaseModel):
    """
    Structured JSON output schema for Principal Architect Agent.
    """
    topology_markdown: str = Field(
        ...,
        description="System topology diagram in Mermaid format, showing gateways, services, and databases."
    )
    design_rationale: str = Field(
        ...,
        description="Detailed technical reasoning and framework design choices supporting the topology."
    )
