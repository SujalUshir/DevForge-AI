"""
Generic Model Context Protocol (MCP) Client using official SDK.
"""

import asyncio
import contextlib
import time
from typing import Any, Dict, List, Optional
import structlog

import sys
import os

def _import_official_mcp():
    original_path = list(sys.path)
    local_parent = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cwd = os.path.abspath(os.getcwd())
    
    exclude_paths = {local_parent, os.path.join(local_parent, "mcp")}
    if cwd.startswith(local_parent):
        exclude_paths.add(cwd)
        
    new_path = []
    for p in sys.path:
        abs_p = os.path.abspath(p) if p else cwd
        if abs_p not in exclude_paths:
            new_path.append(p)
            
    sys.path = new_path
    
    # Save and temporarily remove local mcp modules from sys.modules
    mcp_modules = {k: v for k, v in sys.modules.items() if k == "mcp" or k.startswith("mcp.")}
    for k in mcp_modules:
        del sys.modules[k]
        
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        return ClientSession, StdioServerParameters, stdio_client
    finally:
        sys.path = original_path
        # Restore local mcp modules in sys.modules
        for k, v in mcp_modules.items():
            sys.modules[k] = v

ClientSession, StdioServerParameters, stdio_client = _import_official_mcp()

from .exceptions import MCPConnectionError, MCPTimeoutError, MCPError

logger = structlog.get_logger(__name__)


class GenericMCPClient:
    """
    A reusable, generic Model Context Protocol (MCP) client.
    
    Establishes and maintains a persistent connection to an MCP server using 
    stdio transport, and coordinates JSON-RPC communication.
    """

    def __init__(
        self,
        command: str,
        args: List[str],
        env: Optional[Dict[str, str]] = None,
        timeout: float = 30.0
    ):
        self.command = command
        self.args = args
        self.env = env
        self.timeout = timeout
        self.session: Optional[ClientSession] = None
        self._exit_stack: Optional[contextlib.AsyncExitStack] = None

    async def connect(self) -> None:
        """
        Establish a persistent connection and initialize the MCP session.
        Does nothing if already connected.
        """
        if self.is_connected():
            return

        logger.info("mcp_client_connecting", command=self.command, args=self.args)
        self._exit_stack = contextlib.AsyncExitStack()
        try:
            server_params = StdioServerParameters(
                command=self.command,
                args=self.args,
                env=self.env
            )
            # Enter stdio_client context manager
            read, write = await self._exit_stack.enter_async_context(stdio_client(server_params))
            # Enter ClientSession context manager
            self.session = await self._exit_stack.enter_async_context(ClientSession(read, write))
            
            # Initialize the session
            await asyncio.wait_for(self.session.initialize(), timeout=self.timeout)
            logger.info("mcp_client_connected")
        except asyncio.TimeoutError as exc:
            await self.disconnect()
            raise MCPTimeoutError(f"Connection to MCP server timed out after {self.timeout}s") from exc
        except Exception as exc:
            await self.disconnect()
            raise MCPConnectionError(f"Failed to connect to MCP server: {str(exc)}") from exc

    async def disconnect(self) -> None:
        """
        Clean up connection and close active session context.
        """
        if self._exit_stack:
            logger.info("mcp_client_disconnecting")
            try:
                await self._exit_stack.aclose()
            except Exception as exc:
                logger.warning("mcp_client_disconnect_error", error=str(exc))
            finally:
                self._exit_stack = None
                self.session = None
            logger.info("mcp_client_disconnected")

    def is_connected(self) -> bool:
        """
        Check if the client is connected with an active session.
        """
        return self.session is not None

    async def list_tools(self) -> List[Any]:
        """
        List tools available on the connected MCP server.
        """
        if not self.is_connected():
            raise MCPConnectionError("MCP client is not connected.")

        logger.debug("mcp_client_list_tools")
        try:
            response = await asyncio.wait_for(self.session.list_tools(), timeout=self.timeout)
            return response.tools
        except asyncio.TimeoutError as exc:
            raise MCPTimeoutError("List tools operation timed out") from exc
        except Exception as exc:
            raise MCPError(f"Failed to list tools: {str(exc)}") from exc

    async def call_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute a tool by name on the connected MCP server.
        
        Args:
            name: The tool name to invoke.
            arguments: Input arguments for the tool.
            
        Returns:
            The tool call result returned by the server.
        """
        if not self.is_connected():
            raise MCPConnectionError("MCP client is not connected.")

        # Exclude sensitive arguments from logging and truncate long string values
        safe_args = {}
        if arguments:
            sensitive_keys = {"token", "password", "secret", "key", "auth"}
            for k, v in arguments.items():
                if any(sk in k.lower() for sk in sensitive_keys):
                    safe_args[k] = "[REDACTED]"
                elif isinstance(v, str):
                    if k == "content":
                        safe_args[k] = f"<Content: {len(v)} chars>"
                    elif len(v) > 200:
                        safe_args[k] = v[:200].encode("ascii", "replace").decode("ascii") + f"... [truncated {len(v) - 200} chars]"
                    else:
                        safe_args[k] = v.encode("ascii", "replace").decode("ascii")
                else:
                    safe_args[k] = v

        logger.info("mcp_client_call_tool_start", tool_name=name, arguments=safe_args)
        start_time = time.monotonic()

        try:
            result = await asyncio.wait_for(
                self.session.call_tool(name, arguments or {}),
                timeout=self.timeout
            )
            duration = time.monotonic() - start_time
            logger.info(
                "mcp_client_call_tool_success",
                tool_name=name,
                duration_seconds=duration,
                success=True
            )
            return result
        except asyncio.TimeoutError as exc:
            duration = time.monotonic() - start_time
            logger.error(
                "mcp_client_call_tool_timeout",
                tool_name=name,
                duration_seconds=duration,
                success=False,
                error="Timeout"
            )
            raise MCPTimeoutError(f"Tool execution '{name}' timed out after {self.timeout}s") from exc
        except Exception as exc:
            duration = time.monotonic() - start_time
            logger.error(
                "mcp_client_call_tool_failure",
                tool_name=name,
                duration_seconds=duration,
                success=False,
                error=str(exc)
            )
            raise MCPError(f"Error calling tool '{name}': {str(exc)}") from exc
