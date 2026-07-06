<div align="center">
  <h1>⚡ DevForge AI</h1>
  <p><strong>An autonomous AI software company that transforms ideas into production-ready engineering blueprints via multi-agent collaboration.</strong></p>
  <p>
    <img src="https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/FastAPI-0.139+-green?logo=fastapi&logoColor=white" alt="FastAPI">
    <img src="https://img.shields.io/badge/Next.js-15+-black?logo=next.js&logoColor=white" alt="Next.js">
    <img src="https://img.shields.io/badge/Google_ADK-v2.3.0-orange?logo=google&logoColor=white" alt="Google ADK">
    <img src="https://img.shields.io/badge/Model_Context_Protocol-v1.28-purple?logo=databricks&logoColor=white" alt="MCP">
    <img src="https://img.shields.io/badge/License-MIT-yellow" alt="MIT License">
  </p>
</div>

---

## 📖 Table of Contents
- [What is DevForge AI?](#what-is-devforge-ai)
- [Motivation](#motivation)
- [System Architecture](#system-architecture)
- [Agent Swarm & Workflow](#agent-swarm--workflow)
- [Screenshots & UI Walkthrough](#screenshots--ui-walkthrough)
- [Google ADK & MCP Integration](#google-adk--mcp-integration)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Environment Variables](#environment-variables)
  - [Running Locally](#running-locally)
- [Verification & Tests](#verification--tests)
- [Demo Script](#demo-script)
- [Future Work](#future-work)
- [License](#license)

---

## What is DevForge AI?

DevForge AI is an autonomous, multi-agent software development platform acting as a virtual software company. Submit a product concept, and a team of 11 specialized AI agents—structured into Planning, Architecture, Engineering, Validation, and Review departments—collaborates to produce a complete, production-ready engineering blueprint and document package. 

**This is not a chatbot. It is a structured AI organization.**

---

## Motivation

Traditional single-prompt code generators and chatbots suffer from key limitations:
1. **Context Drift:** As conversations grow, the model loses track of requirements and introduces regressions.
2. **Lack of Peer Review:** A single model generation does not undergo checks and balances before writing files.
3. **No Sandbox Controls:** Writing files directly on the host machine bypasses security boundaries.

**DevForge AI** addresses these problems by:
* Dividing tasks among **11 specialized agents** with strict input/output boundaries.
* Implementing a **Shared Project Context** with an asynchronous lock enforcing the *Single Writer Principle*.
* Integrating **Google ADK** for robust structured output schemas.
* Routing all disk operations through a **Filesystem MCP (Model Context Protocol) Server** to enforce path traversal safety and restrict access to the target workspace.

---

## System Architecture

The platform runs as a Next.js web application connected to a local FastAPI service. The orchestrator delegates tasks to the Google ADK swarm, validates schemas, and utilizes the Filesystem MCP client to scaffold directories.

```mermaid
graph TD
    User([User Browser])
    
    subgraph Frontend [Next.js Web Workspace]
        UI[Interactive Portal]
        SSE[SSE Stream Connection]
        EXP[Blueprint Explorer]
        UI -->|POST /generate| SSE
        EXP -->|GET /artifacts| UI
    end
    
    subgraph Backend [FastAPI Server]
        API[API Router]
        BGS[Async Background Task Worker]
        CM[Shared Project ContextManager]
        API -->|Starts| BGS
        BGS -->|Mutates State| CM
    end
    
    subgraph Swarm [Autonomous Agent Swarm - Google ADK]
        CEO[CEO Agent]
        PLAN[Planning Dept: Product Lead, Market Analyst, Design Lead]
        ARCH[Architecture Dept: Principal Architect]
        ENG[Engineering Dept: Backend Lead, Frontend Lead]
        VAL[Validation Dept: Security Lead, QA Lead, Platform Engineer]
        REV[Review Dept: Engineering Director]
        
        CEO --> PLAN --> ARCH --> ENG --> VAL --> REV
    end

    subgraph Tools [Local Environment Bridges]
        MCP[Filesystem MCP Client]
        Disk[(Local Workspace Directory)]
    end
    
    User -->|Accesses| UI
    UI -->|HTTP Requests| API
    BGS -->|Subscribes & Streams| SSE
    BGS -->|Executes Swarm| Swarm
    Swarm -->|Collaborates via Lock| CM
    BGS -->|Invokes Scaffolding| MCP
    MCP -->|Writes Files| Disk
    Disk -->|Read Back| EXP
```

---

## Agent Swarm & Workflow

DevForge AI organizes its workforce into five distinct departments, overseen by the CEO and audited by the Engineering Director:

| Department | Role | Responsibility | Input Context | Output Fields |
| :--- | :--- | :--- | :--- | :--- |
| — | **CEO** | Orchestrates bootstrap & refines project vision | User Idea | Project metadata |
| **Planning** | **Product Lead** | Functional PRD & user stories | Metadata | `prd_markdown` |
| **Planning** | **Market Analyst** | Competitor analysis & SWOT brief | Metadata | `competitor_brief_markdown` |
| **Planning** | **Design Lead** | UX layout & wireframe specifications | Metadata | `ux_layout_specs` |
| **Architecture** | **Principal Architect** | System topology & architectural design | Planning outputs | `topology_markdown`, `design_rationale` |
| **Engineering** | **Backend Lead** | Database DDL & API OpenAPI schemas | Architecture outputs | `api_spec_yaml`, `database_schema_sql` |
| **Engineering** | **Frontend Lead** | UI router skeletons & component design | Architecture outputs | `routing`, `frontend_pages`, `components`, `layout` |
| **Validation** | **Security Lead** | Threat modeling & validation checks | Code artifacts | `security_report_markdown` |
| **Validation** | **QA Lead** | Integration and unit testing scenarios | Code artifacts | `test_plan_markdown` |
| **Validation** | **Platform Engineer** | Dockerfiles & CI/CD workflows | Code artifacts | `dockerfile`, `docker_compose_yml` |
| **Review** | **Engineering Director**| Final sign-off & quality gate approval | Full Context | `approved`, `reviewer_feedback` |

### Revision Loops & Quality Gates
If the **Engineering Director** rejects the generated blueprints (e.g., security flaws or database schema mismatches), the orchestrator transitions back to the **Engineering** phase with detailed feedback. This revision loop is capped at a maximum of 2 attempts to ensure execution bounds.

---

## Screenshots & UI Walkthrough

The Next.js frontend uses a premium, modern glassmorphic theme designed to provide maximum visibility into the agent swarm:

### 1. The Landing Portal
* **Visuals:** Clean, dark grid design featuring card overlays for all 11 agent roles.
* **Functionality:** Input form to launch custom parameters, along with a "Try Sample Project" quick-start button.

### 2. Live Workspace Dashboard
* **Visuals:** Left-side department timeline highlighting active phases (Planning, Architecture, etc.), and a central active agent status card.
* **Functionality:** Subscribes to the FastAPI Server-Sent Events (SSE) stream, outputting real-time log actions.

### 3. Blueprint Explorer & Downloader
* **Visuals:** Split-pane interface containing a directory tree of generated artifacts and an integrated syntax-highlighted code viewer.
* **Functionality:** Real-time markdown rendering and a single-click "Download ZIP" builder bundle.

---

## Google ADK & MCP Integration

### Google Agent Development Kit (ADK)
All agents leverage the Google Python ADK (`google-adk` v2.3.0) to maintain structured output formatting:
```python
agent = LlmAgent(
    name="devforge_structured_agent",
    model="gemini-2.5-flash",
    instruction=system_instruction,
    output_schema=response_schema,
    output_key="structured_response"
)
runner = Runner(app_name="devforge-ai", agent=agent, session_service=self.session_service)
async for event in runner.run_async(...):
    # Parse state_delta for Pydantic schema validation
```

### Model Context Protocol (MCP)
To guarantee path validation and workspace safety, all disk operations are dispatched to an official `@modelcontextprotocol/server-filesystem` server executing over standard I/O (stdio). Absolute path resolution prevents path traversal outside the sandboxed `./workspace/` directory:
```python
# Path traversal validation check
resolved = Path(path_str).resolve()
if not resolved.is_relative_to(self.workspace_root):
    raise MCPPathTraversalError("Access denied: path traversal attempt")
```

---

## Technology Stack

* **Frontend:** Next.js 15 (React 19) + TypeScript + Tailwind CSS (v4)
* **Backend:** FastAPI (Python 3.11+) + Pydantic v2 + structlog
* **Orchestration:** Google Agent Development Kit (ADK)
* **Model:** Gemini 2.5 Flash / Gemini 2.0 Flash
* **Protocol:** Model Context Protocol (MCP) stdio Filesystem
* **Package Manager:** uv (Python) / npm (Node.js)

---

## Project Structure

```
DevForge-AI/
├── apps/
│   ├── backend/                # FastAPI + Google ADK backend
│   │   ├── agents/             # 11 department agent classes
│   │   ├── api/                # FastAPI routing & SSE streams
│   │   ├── context/            # Shared Project Context manager
│   │   ├── generator/          # Scaffolder invoking Filesystem MCP
│   │   ├── mcp/                # Generic and Filesystem MCP clients
│   │   ├── prompts/            # System prompt markdown files
│   │   └── main.py             # FastAPI entrypoint
│   └── frontend/               # Next.js frontend workspace
│       └── src/app/page.tsx    # Full UI: landing portal, live dashboard, artifact explorer
├── packages/
│   ├── shared-schemas/         # Shared Pydantic data schemas
│   └── mcp-client/             # Placeholder packaging library
├── docs/                       # PRDs & System Architecture
├── tests/
│   └── backend-unit/           # Unit tests covering context, adapters, and agents
└── .env.example                # Clean environment variables configuration
```

---

## Getting Started

### Prerequisites
* Python 3.11+
* Node.js 20+
* [uv](https://docs.astral.sh/uv/) python manager
* A Gemini API Key from [Google AI Studio](https://aistudio.google.com/app/apikey)

### Environment Variables
Copy `.env.example` to `.env` in the root and add your Gemini API Key:
```bash
cp .env.example .env
```

| Variable | Description | Default |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | Your Google Gemini API key from Google AI Studio | `""` |
| `MOCK_LLM` | Set to `true` to run offline with mock agent responses (no API calls) | `false` |
| `LOG_LEVEL` | Application log verbosity (`DEBUG` / `INFO` / `WARNING`) | `INFO` |
| `OUTPUT_DIR` | Directory where generated project blueprints are written | `./workspace` |
| `MAX_REVISION_ATTEMPTS` | Maximum Engineering Director revision cycles before failure | `2` |

### Running Locally

#### 1. Start the Backend
```bash
cd apps/backend
uv sync
uv run uvicorn main:app --reload --port 8000
```
FastAPI runs on `http://127.0.0.1:8000`. You can inspect endpoints via `/docs`.

#### 2. Start the Frontend
```bash
cd apps/frontend
npm install
npm run dev
```
Open `http://localhost:3000` to interact with the workspace portal.

---

## Verification & Tests

To execute the 16 unit test suites covering context synchronization, adapters, and prompt managers:
```bash
cd apps/backend
uv run pytest
```

---

## Demo Script

This script outlines a 5-minute walkthrough for the Google Capstone submission:

* **0:00 - 1:00 (Introduction):** Highlight the platform overview, motivation, and system architecture. Showcase the Next.js landing portal.
* **1:00 - 2:00 (Startup):** Click "⚡ Try Sample Project". Point out how metadata is initialized in the shared context block.
* **2:00 - 3:30 (Live Progress):** Highlight the Server-Sent Events (SSE) log timeline. Explain the sequential and parallel department phases.
* **3:30 - 4:30 (Blueprint Explorer):** When completed, click through files (`PRD.md`, `database_schema.sql`, `api_spec.yaml`) in the code viewer.
* **4:30 - 5:00 (ZIP Download):** Click "Download Blueprint" to compress and download the file bundle.

---

## Future Work

* **GitHub MCP Publishing:** Implement V2 roadmap to directly push scaffolded blueprints to private/public repositories.
* **AWS S3 Cloud Persistence:** Transition context manager from local files to S3 buckets.
* **Mock Compilation Sandbox:** Build an execution container executing backend unit tests against the generated skeletal code.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
