"""
Agent interface specifications using Typing Protocol.
"""

from typing import Protocol, runtime_checkable
from context.manager import ContextManager
from agents.models import AgentResponse


@runtime_checkable
class AgentInterface(Protocol):
    """
    Protocol defining the basic lifecycle interface of any agent.
    Allows duck-typing checks for agent components.
    """
    @property
    def name(self) -> str:
        """The identifier name of the agent."""
        ...

    @property
    def department(self) -> str:
        """The company department this agent is placed under."""
        ...

    async def run(self, context_manager: ContextManager) -> AgentResponse:
        """
        Runs the full standardized lifecycle pipeline:
        initialize -> execute -> validate -> complete/retry -> cleanup
        """
        ...
