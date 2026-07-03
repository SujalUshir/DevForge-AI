"""
Projects management API routes.

Handles:
- POST /api/projects/generate: Initiate the multi-agent forge pipeline in the background.
- GET /api/projects/{project_id}/status: Retrieve current context status details.
- GET /api/projects/{project_id}/stream: SSE event stream delivering real-time agent logs.
- GET /api/projects/{project_id}/artifacts: Retrieve list of generated file blueprints and contents.
- GET /api/projects/{project_id}/download: Compress generated files to ZIP and download.
"""

import asyncio
import json
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, Any, List
from uuid import UUID
import structlog

from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field

from config import settings
from context.manager import ContextManager
from context.schema import ProjectStatus, ExecutionPhase
from orchestrator.orchestrator import Orchestrator
from generator.pipeline import ArtifactGenerator
from agents.llm_adapter import LLMAdapter
from agents.ceo import CEOAgent
from agents.planning import ProductLeadAgent, MarketAnalystAgent, DesignLeadAgent
from agents.architecture import PrincipalArchitectAgent
from agents.mock_agents import (
    MockBackendLead,
    MockFrontendLead,
    MockSecurityLead,
    MockQALead,
    MockPlatformEngineer,
    MockEngineeringDirector
)

logger = structlog.get_logger(__name__)
router = APIRouter()

# In-memory dictionary tracking running project ContextManagers
active_contexts: Dict[str, ContextManager] = {}

# In-memory dictionary storing event queues for active SSE streams
active_event_queues: Dict[str, List[asyncio.Queue]] = {}


# ── Schemas ──────────────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    project_name: str = Field(..., json_schema_extra={"example": "PayFlow Portal"})
    user_idea: str = Field(..., json_schema_extra={"example": "An online dashboard tracking payment status details."})
    frontend_stack: str = Field(default="Next.js + Tailwind")
    backend_stack: str = Field(default="FastAPI")
    database_stack: str = Field(default="PostgreSQL")


class GenerateResponse(BaseModel):
    project_id: UUID
    status: ProjectStatus


class StatusResponse(BaseModel):
    project_id: UUID
    project_name: str
    status: ProjectStatus
    current_phase: ExecutionPhase
    progress: int
    active_agents: List[str]


# ── Execution Worker ─────────────────────────────────────────────────────────

async def run_pipeline_worker(project_id: str, context_manager: ContextManager):
    """
    Background worker orchestrating the multi-agent execution pipeline.
    """
    logger.info("background_worker_start", project_id=project_id)
    
    # 1. Initialize orchestrator
    orchestrator = Orchestrator(context_manager=context_manager)
    
    # Subscribe queue updates to broadcast to active SSE connections
    def event_callback(event):
        queues = active_event_queues.get(project_id, [])
        for q in queues:
            q.put_nowait(event)

    orchestrator.subscribe(event_callback)

    # 2. Register concrete agents (running under LLM Adapter mock mode)
    adapter = LLMAdapter()
    orchestrator.register_agent("CEO Agent", CEOAgent(llm_adapter=adapter))
    orchestrator.register_agent("Product Lead", ProductLeadAgent(llm_adapter=adapter))
    orchestrator.register_agent("Market Analyst", MarketAnalystAgent(llm_adapter=adapter))
    orchestrator.register_agent("Design Lead", DesignLeadAgent(llm_adapter=adapter))
    orchestrator.register_agent("Principal Architect", PrincipalArchitectAgent(llm_adapter=adapter))

    # 3. Register mock downstreams
    orchestrator.register_agent("Backend Lead", MockBackendLead())
    orchestrator.register_agent("Frontend Lead", MockFrontendLead())
    orchestrator.register_agent("Security Lead", MockSecurityLead())
    orchestrator.register_agent("QA Lead", MockQALead())
    orchestrator.register_agent("Platform Engineer", MockPlatformEngineer())
    orchestrator.register_agent("Engineering Director", MockEngineeringDirector())

    try:
        # Run CEO Agent manual bootstrap
        ceo_agent = orchestrator.agents["CEO Agent"]
        await ceo_agent.run(context_manager)
        
        # Execute pipeline
        success = await orchestrator.execute_pipeline()
        
        if success:
            # Generate physical blueprints on disk
            logger.info("background_worker_generating_artifacts", project_id=project_id)
            final_context = context_manager.get_context_copy()
            workspace_dir = settings.output_dir / project_id
            generator = ArtifactGenerator(context=final_context, output_dir=workspace_dir)
            generator.generate_package()
            
            logger.info("background_worker_success", project_id=project_id)
        else:
            logger.error("background_worker_failed_execution", project_id=project_id)

    except Exception as exc:
        logger.exception("background_worker_unhandled_error", project_id=project_id, error=str(exc))
        # Ensure status transitions to FAILED
        await context_manager.acquire_lock("CEO")
        await context_manager.update_project_status("CEO", ProjectStatus.FAILED)
        await context_manager.set_active_phase("CEO", ExecutionPhase.FAILED)
        context_manager.release_lock("CEO")
        
        # Dispatch fail event to stream queues
        event_callback({
            "event": "pipeline_failed",
            "data": {"error": f"Unhandled worker failure: {str(exc)}"},
            "project_id": project_id
        })


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/generate", response_model=GenerateResponse)
async def generate_project(req: GenerateRequest, background_tasks: BackgroundTasks):
    """
    Initialize a new project context and spawn the agent execution worker in the background.
    """
    project_id_str = None
    
    # Initialize workspace metadata folders
    workspace_dir = settings.output_dir
    workspace_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a new context manager instance
    context_manager = ContextManager.create_new(
        project_name=req.project_name,
        user_idea=req.user_idea,
        frontend_stack=req.frontend_stack,
        backend_stack=req.backend_stack,
        database_stack=req.database_stack,
        persist_dir=workspace_dir
    )
    
    ctx = context_manager.get_context_copy()
    project_id_str = str(ctx.metadata.project_id)

    active_contexts[project_id_str] = context_manager
    active_event_queues[project_id_str] = []

    # Run the agent execution loop in the background
    background_tasks.add_task(run_pipeline_worker, project_id_str, context_manager)

    return GenerateResponse(
        project_id=ctx.metadata.project_id,
        status=ctx.metadata.status
    )


@router.get("/{project_id}/status", response_model=StatusResponse)
async def get_project_status(project_id: str):
    """
    Query the current progress state parameters of a project.
    """
    if project_id not in active_contexts:
        raise HTTPException(status_code=404, detail="Project ID not found.")

    ctx_manager = active_contexts[project_id]
    ctx = ctx_manager.get_context_copy()
    
    # Calculate simple mockup progress percentage based on current execution phase
    phase_progress_map = {
        ExecutionPhase.PLANNING: 20,
        ExecutionPhase.ARCHITECTURE: 45,
        ExecutionPhase.ENGINEERING: 65,
        ExecutionPhase.VALIDATION: 85,
        ExecutionPhase.REVIEW: 95,
        ExecutionPhase.COMPLETED: 100,
        ExecutionPhase.FAILED: 0
    }
    progress = phase_progress_map.get(ctx.execution_state.current_phase, 0)

    return StatusResponse(
        project_id=ctx.metadata.project_id,
        project_name=ctx.metadata.project_name,
        status=ctx.metadata.status,
        current_phase=ctx.execution_state.current_phase,
        progress=progress,
        active_agents=ctx.execution_state.active_agents
    )


@router.get("/{project_id}/stream")
async def get_project_stream(project_id: str):
    """
    Server-Sent Events (SSE) stream yielding agent action logs in real-time.
    """
    if project_id not in active_contexts:
        raise HTTPException(status_code=404, detail="Project ID not found.")

    queue = asyncio.Queue()
    active_event_queues[project_id].append(queue)

    async def event_generator():
        try:
            # Yield initial connect signal
            yield f"data: {json.dumps({'event': 'connected', 'data': {}})}\n\n"
            
            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event)}\n\n"
                
                # Close connection upon pipeline completion/failure
                if event.get("event") in ("pipeline_completed", "pipeline_failed"):
                    break
        except asyncio.CancelledError:
            logger.info("sse_connection_cancelled", project_id=project_id)
        finally:
            if project_id in active_event_queues and queue in active_event_queues[project_id]:
                active_event_queues[project_id].remove(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/{project_id}/artifacts")
async def get_project_artifacts(project_id: str):
    """
    Inspect the generated blueprint folder and return file names, contents, and types.
    """
    if project_id not in active_contexts:
        raise HTTPException(status_code=404, detail="Project ID not found.")

    ctx_manager = active_contexts[project_id]
    ctx = ctx_manager.get_context_copy()
    
    if ctx.metadata.status != ProjectStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Project generation is not completed yet.")

    workspace_dir = settings.output_dir / project_id
    if not workspace_dir.exists():
        raise HTTPException(status_code=404, detail="Artifact workspace files could not be found on disk.")

    artifacts = []
    # Read files from disk dynamically
    for filepath in workspace_dir.iterdir():
        if filepath.is_file() and filepath.suffix in (".md", ".yaml", ".sql", ".txt"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                
                lang_map = {
                    ".md": "markdown",
                    ".yaml": "yaml",
                    ".sql": "sql"
                }
                artifacts.append({
                    "name": filepath.name,
                    "content": content,
                    "language": lang_map.get(filepath.suffix, "text")
                })
            except Exception as exc:
                logger.error("error_reading_artifact_file", filename=filepath.name, error=str(exc))

    return artifacts


@router.get("/{project_id}/download")
async def download_project_bundle(project_id: str):
    """
    Compress the generated workspace directory files into a ZIP archive and return it.
    """
    if project_id not in active_contexts:
        raise HTTPException(status_code=404, detail="Project ID not found.")

    ctx_manager = active_contexts[project_id]
    ctx = ctx_manager.get_context_copy()
    
    if ctx.metadata.status != ProjectStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Project generation is not completed yet.")

    workspace_dir = settings.output_dir / project_id
    if not workspace_dir.exists() or not any(workspace_dir.iterdir()):
        raise HTTPException(status_code=404, detail="No artifacts found to pack.")

    # Create temporary zip archive
    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    temp_zip_path = Path(temp_zip.name)
    temp_zip.close()

    try:
        with zipfile.ZipFile(temp_zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for filepath in workspace_dir.iterdir():
                if filepath.is_file():
                    z.write(filepath, arcname=filepath.name)

        filename = f"{ctx.metadata.project_name.lower().replace(' ', '-')}-blueprint.zip"
        return FileResponse(
            path=str(temp_zip_path),
            filename=filename,
            media_type="application/zip"
        )
    except Exception as exc:
        logger.error("zip_compression_failed", error=str(exc))
        if temp_zip_path.exists():
            temp_zip_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to create zip bundle: {str(exc)}")
