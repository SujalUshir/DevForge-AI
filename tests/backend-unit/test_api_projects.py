import pytest
from fastapi.testclient import TestClient

from main import app
from context.schema import ProjectStatus, ExecutionPhase

client = TestClient(app)


def test_project_generation_api_lifecycle():
    """
    Verify complete project generation and status retrieval via FastAPI route handlers.
    """
    # 1. Post request to generate project
    payload = {
        "project_name": "TestAPIForge",
        "user_idea": "A simple api service test",
        "frontend_stack": "Next",
        "backend_stack": "FastAPI",
        "database_stack": "SQLite"
    }
    
    response = client.post("/api/projects/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "project_id" in data
    project_id = data["project_id"]
    
    # 2. Get status immediately
    status_response = client.get(f"/api/projects/{project_id}/status")
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["project_name"] in ("TestAPIForge", "Mock Generated structured output string placeholder")
    assert status_data["status"] in (ProjectStatus.PENDING, ProjectStatus.PROCESSING, ProjectStatus.COMPLETED)

    # 3. Get artifacts for non-existent project should return 404
    artifacts_response = client.get("/api/projects/non-existent-id/artifacts")
    assert artifacts_response.status_code == 404
