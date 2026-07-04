"""
DevForge AI — CLI Demonstration Script.

Runs the multi-agent forge pipeline sequentially using a combination of concrete
Planning & Architecture agents (running under the LLM Adapter mock mode)
and mock downstream agents, then exports the blueprints via the Artifact Generator.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend root to import path if running directly
sys.path.append(str(Path(__file__).parent.resolve()))

from context.manager import ContextManager
from orchestrator.orchestrator import Orchestrator
from agents.llm_adapter import LLMAdapter
from agents.ceo import CEOAgent
from agents.planning import ProductLeadAgent, MarketAnalystAgent, DesignLeadAgent
from agents.architecture import PrincipalArchitectAgent
from agents.engineering import BackendLeadAgent, FrontendLeadAgent
from generator.pipeline import ArtifactGenerator

# Downstream mocks to complete the pipeline
from agents.mock_agents import (
    MockSecurityLead,
    MockQALead,
    MockPlatformEngineer,
    MockEngineeringDirector
)


def log_event(event_payload: dict) -> None:
    """Prints streaming orchestrator lifecycle events to the console."""
    event = event_payload.get("event")
    data = event_payload.get("data", {})
    
    if event == "pipeline_started":
        print("\n[Orchestrator] Starting DevForge execution pipeline...")
    elif event == "phase_started":
        print(f"\n[Phase Transition] Entering phase: {data.get('phase')}")
    elif event == "agent_started":
        print(f"   [+] [{data.get('agent')}] Starting task...")
    elif event == "agent_completed":
        print(f"   [x] [{data.get('agent')}] Completed successfully.")
    elif event == "agent_failed":
        print(f"   [-] [{data.get('agent')}] Failed: {data.get('error')}")
    elif event == "revision_triggered":
        print(f"\n[!] [Revision Gated] Director rejected. Revision loop {data.get('revision')}. Feedback: {data.get('feedback')}")
    elif event == "pipeline_completed":
        print("\n[Orchestrator] Multi-agent forge pipeline completed successfully!")
    elif event == "pipeline_failed":
        print(f"\n[-] [Orchestrator] Pipeline execution failed: {data.get('error')}")


async def main():
    print("=" * 60)
    print("             WELCOME TO DEVFORGE AI CLI DEMO")
    print("=" * 60)

    # 1. Gather user input idea parameters
    user_idea = (
        "A developer platform dashboard matching codegen templates with docker environments, "
        "providing a pipeline monitor panel and secret scanner tools."
    )
    project_name = "DevForge Dashboard"
    
    print(f"\nIdea: '{user_idea}'\n")

    # 2. Setup output workspace folders
    output_dir = Path(__file__).parent.resolve() / "workspace"
    try:
        if output_dir.exists():
            for f in output_dir.iterdir():
                if f.is_file():
                    try:
                        f.unlink()
                    except Exception:
                        pass
    except Exception as exc:
        print(f"Warning: Could not clear existing workspace files: {str(exc)}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 3. Create context manager
    ctx_manager = ContextManager.create_new(
        project_name=project_name,
        user_idea=user_idea,
        frontend_stack="Next.js + Tailwind",
        backend_stack="FastAPI",
        database_stack="PostgreSQL",
        persist_dir=output_dir
    )

    # Ensure mock mode is default for demo run (works offline)
    os.environ["MOCK_LLM"] = "true"
    adapter = LLMAdapter()

    # 4. Initialize Orchestrator and register agents
    orchestrator = Orchestrator(context_manager=ctx_manager)
    orchestrator.subscribe(log_event)

    # Register concrete agents
    orchestrator.register_agent("CEO Agent", CEOAgent(llm_adapter=adapter))
    orchestrator.register_agent("Product Lead", ProductLeadAgent(llm_adapter=adapter))
    orchestrator.register_agent("Market Analyst", MarketAnalystAgent(llm_adapter=adapter))
    orchestrator.register_agent("Design Lead", DesignLeadAgent(llm_adapter=adapter))
    orchestrator.register_agent("Principal Architect", PrincipalArchitectAgent(llm_adapter=adapter))

    orchestrator.register_agent("Backend Lead", BackendLeadAgent(llm_adapter=adapter))
    orchestrator.register_agent("Frontend Lead", FrontendLeadAgent(llm_adapter=adapter))

    # Register downstream mock agents
    orchestrator.register_agent("Security Lead", MockSecurityLead())
    orchestrator.register_agent("QA Lead", MockQALead())
    orchestrator.register_agent("Platform Engineer", MockPlatformEngineer())
    orchestrator.register_agent("Engineering Director", MockEngineeringDirector())

    # 5. Bootstrapping: CEO Agent runs first to refine details
    print("[CEO Agent] Running initial alignment and bootstrapping...")
    ceo_res = await orchestrator.agents["CEO Agent"].run(ctx_manager)
    print(f"   refined name: {ceo_res.output_data.get('refined_project_name')}")
    print(f"   vision: {ceo_res.output_data.get('project_vision')}\n")

    # 6. Execute full pipeline
    success = await orchestrator.execute_pipeline()
    if not success:
        print("\nForge failed. Exiting.")
        sys.exit(1)

    # 7. Generate physical artifacts via Artifact Generator
    print("\n[Artifact Scaffolder] Writing generated engineering blueprints to output folder...")
    final_context = ctx_manager.get_context_copy()
    generator = ArtifactGenerator(context=final_context, output_dir=output_dir)
    written_files = await generator.generate_package()

    print("\n" + "=" * 50)
    print(f"Blueprinted workspace: {output_dir}")
    print("Written Files:")
    for f in written_files:
        print(f"  - {f.name} ({f.stat().st_size} bytes)")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
