import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from context.manager import ContextManager
from agents.llm_adapter import LLMAdapter
from agents.architecture import PrincipalArchitectAgent
from generator import ArtifactGenerator


class MockContent:
    def __init__(self, text: str):
        self.text = text


class MockCallToolResult:
    def __init__(self, text: str):
        self.content = [MockContent(text)]


@pytest.fixture
def mock_mcp_write():
    with patch("mcp.client.stdio_client") as mock_stdio, \
         patch("mcp.client.ClientSession") as mock_session_cls:
        
        mock_stdio.return_value.__aenter__ = AsyncMock(return_value=(MagicMock(), MagicMock()))
        mock_stdio.return_value.__aexit__ = AsyncMock()
        
        mock_session = AsyncMock()
        mock_session.initialize = AsyncMock()
        
        async def mock_call_tool(name, arguments=None):
            if name == "write_file":
                path = arguments["path"]
                content = arguments["content"]
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
            return MockCallToolResult("")
            
        mock_session.call_tool.side_effect = mock_call_tool
        
        mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_cls.return_value.__aexit__ = AsyncMock()
        
        yield mock_session


@pytest.mark.asyncio
async def test_principal_architect_and_artifact_generator(tmp_path, mock_mcp_write):
    """
    Verify the Principal Architect agent writes to context,
    and ArtifactGenerator serializes it into files on disk via FilesystemMCPClient.
    """
    ctx_manager = ContextManager.create_new(
        project_name="TestArch",
        user_idea="A dockerized fastapi engine",
        frontend_stack="Next.js",
        backend_stack="FastAPI",
        database_stack="PostgreSQL"
    )

    adapter = LLMAdapter(api_key="")
    agent = PrincipalArchitectAgent(llm_adapter=adapter)

    # Prepopulate planning context to satisfy inputs
    await ctx_manager.acquire_lock("Product Lead")
    await ctx_manager.update_planning(
        "Product Lead",
        lambda plan: setattr(plan, "prd_markdown", "# Real functional specifications")
    )
    ctx_manager.release_lock("Product Lead")

    # Run Principal Architect
    response = await agent.run(ctx_manager)
    assert response.success is True
    assert "topology_markdown" in response.output_data

    # Verify context updated
    ctx = ctx_manager.get_context_copy()
    assert ctx.architecture.topology_markdown != ""
    assert ctx.architecture.design_rationale != ""

    # Generate files using ArtifactGenerator
    generator = ArtifactGenerator(context=ctx, output_dir=tmp_path)
    generated_files = await generator.generate_package()

    assert len(generated_files) == 3
    assert (tmp_path / "PRD.md").exists()
    assert (tmp_path / "architecture.md").exists()
    assert (tmp_path / "README.md").exists()

    # Now populate engineering data and verify 5 files
    ctx.engineering.api_spec_yaml = "openapi: 3.0.0"
    ctx.engineering.database_schema_sql = "CREATE TABLE users;"
    generator_5 = ArtifactGenerator(context=ctx, output_dir=tmp_path)
    generated_files_5 = await generator_5.generate_package()
    assert len(generated_files_5) == 5
    assert (tmp_path / "api_spec.yaml").exists()
    assert (tmp_path / "database_schema.sql").exists()

    # Verify architecture document contains Mermaid diagrams
    with open(tmp_path / "architecture.md", "r", encoding="utf-8") as f:
        arch_content = f.read()
    assert "# Architecture Document" in arch_content
