"""
Model Context Protocol (MCP) Custom Exception Hierarchy.
"""

class MCPError(Exception):
    """Base exception class for all Model Context Protocol (MCP) errors."""
    pass


class MCPConnectionError(MCPError):
    """Raised when connecting to or communicating with an MCP server fails."""
    pass


class MCPValidationError(MCPError):
    """Raised when validation of MCP inputs, outputs, or constraints fails."""
    pass


class MCPPathTraversalError(MCPValidationError):
    """Raised when an operation attempts path traversal outside the sandboxed workspace."""
    pass


class MCPTimeoutError(MCPError):
    """Raised when an MCP operation or connection times out."""
    pass
