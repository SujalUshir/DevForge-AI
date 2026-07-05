"""
Filesystem Model Context Protocol (MCP) Client Wrapper.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import structlog

from config import settings
from .client import GenericMCPClient
from .exceptions import MCPValidationError, MCPPathTraversalError

logger = structlog.get_logger(__name__)


class FilesystemMCPClient:
    """
    Wrapper client around filesystem tools utilizing GenericMCPClient.
    Connects to the official @modelcontextprotocol/server-filesystem server.
    """

    def __init__(
        self,
        workspace_root: Optional[Union[str, Path]] = None,
        read_only: bool = False,
        timeout: float = 30.0
    ):
        raw_root = workspace_root or settings.output_dir
        self.workspace_root = Path(raw_root).resolve()
        self.read_only = read_only

        # Ensure workspace root exists
        self.workspace_root.mkdir(parents=True, exist_ok=True)

        command = settings.mcp_node_command
        args = ["-y", settings.filesystem_mcp_package, str(self.workspace_root)]

        self.client = GenericMCPClient(command=command, args=args, timeout=timeout)

    async def connect(self) -> None:
        """Connect to the filesystem MCP server."""
        await self.client.connect()

    async def disconnect(self) -> None:
        """Disconnect from the filesystem MCP server."""
        await self.client.disconnect()

    def is_connected(self) -> bool:
        """Check connection status."""
        return self.client.is_connected()

    def _validate_path(self, path_str: str) -> Path:
        """
        Validates path inputs, preventing path traversal outside the workspace root.
        """
        p = Path(path_str)

        if p.is_absolute():
            try:
                resolved_path = p.resolve()
            except Exception:
                resolved_path = p.absolute()
        else:
            try:
                resolved_path = (self.workspace_root / p).resolve()
            except Exception:
                resolved_path = (self.workspace_root / p).absolute()

        try:
            resolved_path.relative_to(self.workspace_root)
        except ValueError as exc:
            raise MCPPathTraversalError(
                f"Path '{path_str}' resolves outside workspace root '{self.workspace_root}'"
            ) from exc

        return resolved_path

    async def read_file(self, path: str) -> str:
        """Read file contents via MCP server."""
        resolved = self._validate_path(path)
        result = await self.client.call_tool("read_file", {"path": str(resolved)})
        return self._extract_text(result)

    async def write_file(self, path: str, content: str) -> None:
        """Write file contents via MCP server."""
        if self.read_only:
            raise MCPValidationError("Cannot write file: MCP client is in read-only mode.")
        
        resolved = self._validate_path(path)
        await self.client.call_tool("write_file", {"path": str(resolved), "content": content})

    async def list_directory(self, path: str) -> str:
        """List files and folders in directory via MCP server."""
        resolved = self._validate_path(path)
        result = await self.client.call_tool("list_directory", {"path": str(resolved)})
        return self._extract_text(result)

    async def create_directory(self, path: str) -> None:
        """Create a new directory via MCP server."""
        if self.read_only:
            raise MCPValidationError("Cannot create directory: MCP client is in read-only mode.")
            
        resolved = self._validate_path(path)
        await self.client.call_tool("create_directory", {"path": str(resolved)})

    def file_exists(self, path: str) -> bool:
        """
        Check if a file exists locally under workspace.
        """
        resolved = self._validate_path(path)
        return resolved.is_file()

    def _extract_text(self, result) -> str:
        """Helper to extract raw text content from CallToolResult."""
        if hasattr(result, "content") and result.content:
            return "".join(block.text for block in result.content if hasattr(block, "text"))
        return ""
