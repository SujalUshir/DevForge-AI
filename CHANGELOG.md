# Changelog

All notable changes to the DevForge AI project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-07-11

### Added
- **Multi-Agent Orchestration SWARM:** Implemented a team of 11 specialized AI agents structured into Planning, Architecture, Engineering, Validation, and Review departments.
- **Google Agent Development Kit (ADK) Integration:** Programmatically integrated `google-adk` v2.3.0 for structured output schema guarantees.
- **Model Context Protocol (MCP) Integration:** Connected the generator pipeline to a stdio-based Filesystem MCP server (`@modelcontextprotocol/server-filesystem`) to restrict disk operations to the targeted `./workspace` sandbox.
- **FastAPI Backend Services:** Added Server-Sent Events (SSE) router, zipfile downloader, and background status workers.
- **Next.js 15 Portal Interface:** Built a glassmorphic dashboard visualizing active swarm status, log streams, and an interactive blueprint code explorer.
- **Comprehensive Unit Tests:** Created 35 unit test suites validating agent lifecycles, prompt security, context lock synchronization, and routing logic.

### Refactored
- **Context Update Handlers:** Refactored multiple agent state-updating callback patterns from lambda expressions using side-effects (list literal setattr calls) to pythonic, clean inner functions.
- **Editable Source Links:** Configured the local `shared-schemas` path dependency as an editable source in backend `pyproject.toml` to prevent stale build cache leaks.

### Fixed
- **Isolated MCP Test Suite Collision:** Resolved import collision in `test_mcp_client.py` where site-packages `mcp` module polluted `sys.modules`, failing test collection when executed in isolation.
