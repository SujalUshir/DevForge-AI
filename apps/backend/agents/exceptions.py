"""
Agent-specific exception definitions.
"""

class AgentError(Exception):
    """Base exception for all agent-related failures."""
    pass


class AgentInitializationError(AgentError):
    """Raised when an agent fails to initialize."""
    pass


class AgentExecutionError(AgentError):
    """Raised when an agent encounters a fatal error during task execution."""
    pass


class AgentValidationError(AgentError):
    """Raised when an agent's output violates the required schema or validation logic."""
    pass
