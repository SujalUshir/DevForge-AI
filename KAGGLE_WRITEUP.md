# DevForge AI

## Subtitle
An autonomous virtual software company driven by the Google Agent Development Kit and Model Context Protocol to translate product concepts into verified, secure engineering blueprints.

## Introduction
Software planning and early-stage systems architecture present significant hurdles for developers and product teams. In the initial phases of any software project, translating a high-level concept into concrete, actionable specifications—such as database schemas, API contracts, deployment files, threat models, and test plans—requires coordinating multiple specialized disciplines. A single engineer or a small startup team must switch contexts constantly, acting sequentially as a product manager, systems architect, backend engineer, security auditor, and QA lead. This context-switching frequently introduces gaps in system design, resulting in database modeling errors, overlooked security vulnerabilities, or missing test strategies.

Existing AI coding assistants, while powerful for code generation, suffer from notable limitations during the system planning phase. Typical chat-based interfaces or single-prompt models operate on a simple one-shot or conversational loop. They lack long-term architectural cohesion, suffer from context drift as discussions grow, and tend to agree with user assumptions without critical review. Furthermore, single-prompt models lack peer feedback mechanisms, meaning they write code and configurations without secondary validation or security auditing. 

I built DevForge AI to bridge this gap. Rather than acting as a simple conversational assistant, my project implements a structured, autonomous AI organization that models a software engineering company. By dividing the generation and verification processes among eleven specialized AI agents, the platform automates the synthesis of comprehensive, multi-file engineering blueprints, ensuring that database schema designs, OpenAPI specifications, and deployment files are synchronized, audited, and verified before they are output.

## Problem Statement
The early phases of software development are plagued by architectural misalignment and design flaws. Solo developers and small teams rarely have the resources to hire dedicated specialists for every stage of development. Consequently, system topology is often designed without formal modeling, API contracts are drafted ad hoc, security policies are deferred, and test planning is neglected. When development begins under these conditions, teams incur massive refactoring costs due to misaligned database relationships, API integration mismatches, and infrastructure security holes.

The target audience for DevForge AI includes solo developers, startup founders, and software engineering teams. For developers, the platform eliminates the initial bootstrapping overhead by providing a unified starter package. For founders, it validates technical viability and generates developer-ready specs. For teams, it accelerates prototyping. Solving this problem matters because it shifts the developer's focus from boilerplate scaffolding and initial design arguments to actual implementation and product differentiation, reducing the time-to-prototype from weeks to minutes.

## Why Multi-Agent Systems?
A single, monolithic LLM prompt is fundamentally insufficient for complex software system design. A single model prompt cannot effectively critique its own system architecture, identify its own security flaws, or build unbiased test scenarios. When a single model is asked to act simultaneously as a designer, builder, and auditor, it trades depth and critical reasoning for broad, generic outputs. It lacks the internal friction required to reject bad decisions.

Multi-agent systems are the right solution because they allow for specialization, division of labor, and peer review. By constraining each agent to a specific role with clear boundaries and dedicated prompt instructions, they maintain focus on their core competencies. The system relies on:
1. Specialization: Agents are dedicated to specific files and domains (e.g., the Security Lead only audits code for vulnerabilities; the database engineer focus is solely on SQL correctness).
2. Collaboration: Agents build on each other's outputs sequentially and in parallel, passing verified context slices forward.
3. Validation: The Validation Department audits configurations before sign-off.
4. Iterative Refinement: The Engineering Director reviews the completed project context and decides whether to approve it or return it to the developers with feedback, establishing a robust quality gate.

## Solution Overview
DevForge AI is an autonomous software development platform operating as a virtual software company. Users input their application concept, select their target frontend, backend, and database stacks, and initiate the generation. The platform coordinates a team of eleven specialized AI agents across five departments—Planning, Architecture, Engineering, Validation, and Review—to collaboratively design and verify a starter project blueprint. 

The output is not just a chat transcript; it is a downloadable engineering blueprint package. This package contains a detailed Product Requirements Document (PRD), a system topology document with visual Mermaid diagrams, a valid OpenAPI 3.0 specification, a database schema SQL DDL file, a security and threat model report, a QA test plan, and DevOps configuration files (Dockerfile and Docker Compose).

## System Architecture
I designed the platform around a decoupled frontend-backend architecture with centralized state management, asynchronous orchestration, and tool sandboxing via MCP.

The presentation layer is hosted in a Next.js 15 frontend application, which provides an interactive web dashboard. When a user submits an idea, the frontend makes a POST request to the FastAPI backend at `/api/projects/generate`. 

The backend orchestrator initializes a ContextManager instance to create a new session, starts the pipeline execution, and returns a unique project ID to the frontend. The frontend immediately connects to a Server-Sent Events (SSE) stream endpoint to receive real-time updates of agent actions, system logs, and department timelines.

Central to the orchestration is the Shared Project Context, a thread-safe, asyncio-locked JSON structure on disk. To prevent context drift and race conditions, the system enforces the Single Writer Principle: only the active agent holding the write lock is permitted to modify the state. Concurrency is handled by allowing parallel agents to write to isolated keys in memory, which the orchestrator merges atomically upon phase completion.

## Agent Workflow
The execution pipeline is coordinated in a sequential-parallel state machine:
1. CEO Agent: Parses the raw user concept, refines the project name, recommends stack parameters, and bootstraps the Shared Context metadata.
2. Planning Department (Parallel): Runs the Product Lead (PRD generator), Market Analyst (competitor and SWOT brief), and Design Lead (UX layout and wireframe specifications) in parallel.
3. Architecture Department (Sequential): The Principal Architect consumes the planning outputs to design the system topology and document the technical design rationale.
4. Engineering Department (Parallel): The Backend Lead compiles the OpenAPI YAML spec and database SQL schema; the Frontend Lead structures the component hierarchy and routing layout.
5. Validation Department (Parallel): The Security Lead audits the engineering schemas for threat models; the QA Lead drafts unit and integration test strategies; the Platform Engineer creates the Dockerfile and Docker Compose configurations.
6. Review Department (Sequential): The Engineering Director evaluates the completed context. If compliance checks fail, the Director rejects the blueprint, triggering a revision loop. The orchestrator returns to the Engineering phase with detailed feedback. To prevent infinite loops, the orchestrator caps revision attempts at two before marking the project as failed.
7. Artifact Generator: Upon approval, the generator connects to the Filesystem MCP client and scaffolds the physical files (`PRD.md`, `architecture.md`, `api_spec.yaml`, `database_schema.sql`, `README.md`) in a sandboxed target workspace directory on the host machine.
8. ZIP Compiler: Packs the generated folder into a ZIP bundle, making it available for download.

## Google ADK Integration
I integrated the official `google-adk` package to manage agent models, session tracking, and structured output schemas. Each agent is configured as a stateful `LlmAgent` and executed via the `Runner` session service. 

By supplying a Pydantic schema class to the ADK `output_schema` configuration, the underlying adapter enforces strict JSON structured output parsing. The ADK runner initiates the async generator loop, yielding state deltas that are validated against the schema before the orchestrator merges them into the main context, eliminating the risk of unstructured text corrupting the execution pipeline.

## Filesystem MCP Integration
File writing is entirely decoupled from the backend application logic. I integrated the Model Context Protocol (MCP) filesystem server `@modelcontextprotocol/server-filesystem` to run locally via `npx` stdio. 

The backend hosts a client wrapper that connects to this filesystem server. When the pipeline finishes, the Artifact Generator sends standardized tool calls (`write_file`, `create_directory`) to the filesystem server to scaffold the folder structure. By delegating all filesystem I/O to the MCP server, the agents operate inside a standardized, tool-driven boundary.

## Technical Implementation
The platform backend utilizes Python's async/await syntax to manage concurrency and non-blocking I/O. The Shared Project Context is loaded dynamically and saved atomically as a JSON database file (`context_{project_id}.json`) to maintain state persistence across server restarts. 

An async lock manager protects the JSON file during writes. FastAPI background tasks handle the agent execution loop, allowing the API to respond instantly to the frontend. The backend streams updates via a Server-Sent Events router, pushing serialized JSON events to the browser.

## Key Features
1. Multi-Agent Collaboration: Eleven distinct agents operate collaboratively under a centralized orchestrator, shifting the human developer's role to that of an auditor.
2. Parallel and Sequential Execution Gates: Concurrency is leveraged during planning, engineering, and validation phases to minimize latency, while sequential gates ensure dependencies are satisfied before transitioning.
3. Strict Structured Outputs: Every agent is bound to a Pydantic response schema, preventing raw text outputs from corrupting the Shared Context.
4. Thread-Safe Shared Context: Managed by an async lock to enforce context isolation and single-writer boundaries.
5. Quality Gate & Revision Loop: The Engineering Director agent acts as an automated reviewer, ensuring cross-file compliance and database/API alignment.
6. Filesystem MCP Sandboxing: Restricts file writing to a normalized path relative to the target workspace, protecting the host machine from path traversal vulnerabilities.
7. Live SSE Log Timeline: Provides full transparency, allowing the user to watch agent debates and logs in real time.
8. Zipped Blueprint Packages: Creates a packaged starter project structure ready for local download.

## Demonstration of Course Concepts

### Multi-Agent System (Google ADK)
The project demonstrates the core engineering concepts of the Kaggle Agents course by using the official `google-adk` package (`LlmAgent` and `Runner`) to build stateful agent loops and validate Pydantic output schemas. This demonstrates how to construct structured multi-agent organizations with clear boundaries rather than simple conversational chatbots.

### Model Context Protocol (MCP)
Disk write operations are decoupled from backend code. All files are generated by launching and communicating with a stdio-based Filesystem MCP server tool, showcasing tool-calling patterns and standardization in modern agent architectures.

### Security Features
I implemented strict path normalization via Python's `pathlib.Path.resolve()`, validating that all targets reside inside the output workspace. This blocks path traversal attempts (e.g. `../etc/passwd`) at the client boundary, preventing agents or input prompts from writing files outside the designated workspace.

### Deployability
Sourced from clean environment configurations (`.env.example`), the backend is fully dockerized and supports running in local mock mode (`MOCK_LLM=true`) to enable zero-quota offline evaluation, ensuring that anyone can run the pipeline without API credentials.

### Agent Skills
Prompts are separated from implementation code and loaded dynamically from markdown files via a custom `PromptLoader` in the `prompts` directory, demonstrating clean configuration design.

### Antigravity
During development, the Antigravity coding assistant was utilized as a pair programmer. I used Antigravity to perform a comprehensive static analysis audit of the repository, refactor the LLM adapter for Google ADK compatibility, verify the Filesystem MCP schema tools, clean up stale files, and synchronize the system documentation before release.

## Technical Challenges
1. Agent Orchestration: Coordinating eleven agents with nested dependencies without causing deadlock was a significant challenge. I solved this by building a centralized, sequential-parallel state machine in `orchestrator.py`.
2. Context sharing: Passing the entire context to every agent risks exceeding token limits and introducing noise. I solved this by slicing the Shared Context, providing each agent only with its required inputs.
3. Structured outputs validation: LLMs often output raw markdown code blocks. I addressed this by wrapping the ADK runner to extract the event text payload and parsing it against Pydantic models with automated retries.
4. Concurrency management: Multiple agents writing to the context simultaneously was resolved by using isolated memory buffers for parallel phases, merging them atomically under a write lock upon phase completion.

## Results
DevForge AI successfully automates the initial planning and design stages of software engineering. By establishing a virtual company of specialized agents, the platform translates a high-level user prompt into a complete, structured blueprint package in under 30 seconds (offline) or in a few minutes (live model calls). 

Multi-agent collaboration proves highly beneficial: by separating roles, the system exposes logical flaws (such as API contracts writing to non-existent database tables) that a single-prompt model would ignore, correcting them automatically in the review loop. For developers and teams, this reduces bootstrapping overhead, ensures compliance with security best practices, and creates clear specifications that can be handed directly to developers or fed into code generators.

## Future Improvements
1. GitHub MCP Integration: I plan to expand the MCP client to connect to a GitHub MCP server, allowing DevForge AI to push generated blueprints directly to remote repositories.
2. Sandboxed Compilation and Linting: I want to introduce an execution worker that runs test suites inside a secure Docker container, feeding compilation and runtime logs back into the revision loop.
3. State Persistence: I plan to transition from local JSON file storage to a relational database (e.g. PostgreSQL) to support concurrent multi-user project generation and project history tracking.
4. Additional Agent Roles: I plan to add database administrators and cloud architects to write Kubernetes configurations and Terraform scripts.

## Conclusion
I built DevForge AI as a multi-agent system on the Google ADK and MCP that automates software system design and scaffolding. By establishing a structured team of specialized agents, enforcing thread-safe state sharing, and routing all operations through a secure MCP server, the project demonstrates a robust implementation of modern AI engineering. It demonstrates that combining Google ADK's structured schemas with MCP's sandboxed environment allows developers to build autonomous systems that are secure, reliable, and production-ready.
