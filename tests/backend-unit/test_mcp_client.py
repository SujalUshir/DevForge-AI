import asyncio
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import sys
import os

def _import_official_mcp_exceptions():
    original_path = list(sys.path)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    local_parent = os.path.abspath(os.path.join(base_dir, "apps", "backend"))
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
    for k in list(sys.modules.keys()):
        if k == "mcp" or k.startswith("mcp."):
            del sys.modules[k]
        
    try:
        from mcp import McpError
        return McpError
    finally:
        sys.path = original_path
        # Remove the official mcp from sys.modules so subsequent imports load the local one
        if "mcp" in sys.modules:
            del sys.modules["mcp"]
        for k in list(sys.modules.keys()):
            if k.startswith("mcp."):
                del sys.modules[k]
        # Restore local mcp modules in sys.modules
        for k, v in mcp_modules.items():
            sys.modules[k] = v

McpError = _import_official_mcp_exceptions()

from mcp import (
    GenericMCPClient,
    FilesystemMCPClient,
    MCPError,
    MCPConnectionError,
    MCPValidationError,
    MCPPathTraversalError,
    MCPTimeoutError,
)


class MockContent:
    def __init__(self, text: str):
        self.text = text


class MockCallToolResult:
    def __init__(self, text: str):
        self.content = [MockContent(text)]


@pytest.fixture
def mock_mcp_session():
    with patch("mcp.client.stdio_client") as mock_stdio, \
         patch("mcp.client.ClientSession") as mock_session_cls:
        
        # Setup mock stdio client context manager
        mock_stdio.return_value.__aenter__ = AsyncMock(return_value=(MagicMock(), MagicMock()))
        mock_stdio.return_value.__aexit__ = AsyncMock()
        
        # Setup mock session
        mock_session = AsyncMock()
        mock_session.initialize = AsyncMock()
        mock_session.list_tools = AsyncMock()
        mock_session.call_tool = AsyncMock()
        
        # Setup mock session context manager
        mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_cls.return_value.__aexit__ = AsyncMock()
        
        yield mock_session


@pytest.mark.asyncio
async def test_generic_client_connection(mock_mcp_session):
    client = GenericMCPClient(command="npx", args=["mock-server"])
    assert not client.is_connected()

    await client.connect()
    assert client.is_connected()
    mock_mcp_session.initialize.assert_called_once()

    await client.disconnect()
    assert not client.is_connected()


@pytest.mark.asyncio
async def test_generic_client_connection_timeout(mock_mcp_session):
    # Make initialize time out
    async def slow_init():
        await asyncio.sleep(2.0)
    mock_mcp_session.initialize.side_effect = slow_init

    client = GenericMCPClient(command="npx", args=["mock-server"], timeout=0.1)
    with pytest.raises(MCPTimeoutError):
        await client.connect()


@pytest.mark.asyncio
async def test_generic_client_connection_failure(mock_mcp_session):
    mock_mcp_session.initialize.side_effect = RuntimeError("Process crashed")

    client = GenericMCPClient(command="npx", args=["mock-server"])
    with pytest.raises(MCPConnectionError):
        await client.connect()


@pytest.mark.asyncio
async def test_generic_client_call_tool(mock_mcp_session):
    mock_mcp_session.call_tool.return_value = MockCallToolResult("success_data")

    client = GenericMCPClient(command="npx", args=["mock-server"])
    await client.connect()

    result = await client.call_tool("some_tool", {"arg1": "val1"})
    assert result.content[0].text == "success_data"
    mock_mcp_session.call_tool.assert_called_once_with("some_tool", {"arg1": "val1"})


@pytest.mark.asyncio
async def test_generic_client_call_tool_failure(mock_mcp_session):
    mock_mcp_session.call_tool.side_effect = RuntimeError("Tool internal error")

    client = GenericMCPClient(command="npx", args=["mock-server"])
    await client.connect()

    with pytest.raises(MCPError):
        await client.call_tool("some_tool")


@pytest.mark.asyncio
async def test_filesystem_path_validation():
    # Setup temporary directory as workspace root
    tmp_root = Path("./mcp_test_workspace").resolve()
    tmp_root.mkdir(exist_ok=True)

    client = FilesystemMCPClient(workspace_root=tmp_root)

    # 1. Valid paths
    assert client._validate_path("hello.txt") == tmp_root / "hello.txt"
    assert client._validate_path("nested/folder/file.txt") == tmp_root / "nested/folder/file.txt"

    # 2. Path Traversal Lexical Check
    with pytest.raises(MCPPathTraversalError):
        client._validate_path("../../secret.txt")

    with pytest.raises(MCPPathTraversalError):
        client._validate_path("nested/../../secret.txt")

    # 3. Absolute Path outside workspace
    with pytest.raises(MCPPathTraversalError):
        # On Windows or Unix, absolute path outside workspace should fail
        client._validate_path("/etc/passwd" if Path("/etc/passwd").is_absolute() else "C:/Windows/System32")

    # Clean up
    try:
        tmp_root.rmdir()
    except Exception:
        pass


@pytest.mark.asyncio
async def test_filesystem_path_resolution():
    tmp_root = Path("./mcp_test_workspace_resolution").resolve()
    tmp_root.mkdir(exist_ok=True)

    client = FilesystemMCPClient(workspace_root=tmp_root)

    # Path containing dot elements should resolve
    resolved = client._validate_path("folder/../file.txt")
    assert resolved == tmp_root / "file.txt"

    try:
        tmp_root.rmdir()
    except Exception:
        pass


@pytest.mark.asyncio
async def test_filesystem_read_only_enforcement(mock_mcp_session):
    tmp_root = Path("./mcp_test_workspace_readonly").resolve()
    tmp_root.mkdir(exist_ok=True)

    client = FilesystemMCPClient(workspace_root=tmp_root, read_only=True)
    await client.connect()

    # Reading should be allowed
    mock_mcp_session.call_tool.return_value = MockCallToolResult("file data")
    content = await client.read_file("test.txt")
    assert content == "file data"

    # Writing should be blocked
    with pytest.raises(MCPValidationError):
        await client.write_file("test.txt", "new content")

    # Directory creation should be blocked
    with pytest.raises(MCPValidationError):
        await client.create_directory("subfolder")

    try:
        tmp_root.rmdir()
    except Exception:
        pass


@pytest.mark.asyncio
async def test_filesystem_operations(mock_mcp_session):
    tmp_root = Path("./mcp_test_workspace_ops").resolve()
    tmp_root.mkdir(exist_ok=True)

    client = FilesystemMCPClient(workspace_root=tmp_root, read_only=False)
    await client.connect()

    # Test file_exists when file does not exist
    assert not client.file_exists("missing.txt")

    # Test read
    mock_mcp_session.call_tool.return_value = MockCallToolResult("some text")
    content = await client.read_file("file.txt")
    assert content == "some text"
    mock_mcp_session.call_tool.assert_called_with("read_file", {"path": str(tmp_root / "file.txt")})

    # Test write
    mock_mcp_session.call_tool.return_value = MockCallToolResult("")
    await client.write_file("file.txt", "hello")
    mock_mcp_session.call_tool.assert_called_with("write_file", {"path": str(tmp_root / "file.txt"), "content": "hello"})

    # Test list_directory
    mock_mcp_session.call_tool.return_value = MockCallToolResult("file.txt\nfolder")
    listing = await client.list_directory(".")
    assert listing == "file.txt\nfolder"
    mock_mcp_session.call_tool.assert_called_with("list_directory", {"path": str(tmp_root)})

    try:
        tmp_root.rmdir()
    except Exception:
        pass
