# DevForge AI — Backend

FastAPI application exposing the multi-agent blueprint generation pipeline.

## Quick Start

```bash
cd apps/backend
uv sync
uv run uvicorn main:app --reload --port 8000
```

The API is available at `http://127.0.0.1:8000`. Interactive docs at `/docs`.

## Environment Variables

Copy `../../.env.example` to `.env` in this directory and set:

| Variable | Description | Default |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | Google AI Studio API key for live agent execution | `""` |
| `MOCK_LLM` | Set `true` to run pipeline offline with mock agent responses | `false` |
| `LOG_LEVEL` | Log verbosity (`DEBUG` / `INFO` / `WARNING`) | `INFO` |
| `OUTPUT_DIR` | Path where generated project blueprints are written | `./workspace` |
| `MAX_REVISION_ATTEMPTS` | Maximum Engineering Director revision cycles | `2` |

## Running Tests

```bash
uv run pytest ../../tests/backend-unit/
```

## Architecture

```
apps/backend/
├── agents/         # 11 specialized ADK agents (CEO, Planning, Architecture, Engineering, Validation, Review)
├── api/            # FastAPI routes + SSE streaming endpoints
├── context/        # SharedProjectContext manager (async lock, JSON persistence)
├── generator/      # ArtifactGenerator — writes blueprints via Filesystem MCP
├── mcp/            # Filesystem MCP client wrapper
├── orchestrator/   # Pipeline orchestrator with phase-gating and revision loop
├── prompts/        # System prompt markdown files loaded by PromptLoader
└── main.py         # FastAPI application entry point
```

## Key Endpoints

| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/api/projects/generate` | Start the agent pipeline in the background |
| `GET` | `/api/projects/{id}/status` | Poll execution phase and progress |
| `GET` | `/api/projects/{id}/stream` | SSE stream of real-time agent events |
| `GET` | `/api/projects/{id}/artifacts` | Fetch generated file names and content |
| `GET` | `/api/projects/{id}/download` | Download generated blueprint as a ZIP |
| `GET` | `/api/health` | Health check |
