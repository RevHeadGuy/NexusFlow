from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_trace_viewer_records_project_events():
    project_response = client.post(
        "/projects",
        json={
            "name": "OpsPilot",
            "description": "AI operations workflow assistant.",
            "idea": "Build an AI operations cockpit that coordinates incident response, status updates, and follow-up tasks across teams.",
        },
    )
    assert project_response.status_code == 201, project_response.text
    project_id = project_response.json()["id"]

    trace_response = client.post(
        f"/projects/{project_id}/traces",
        json={
            "event": "research_started",
            "stage": "idea_discovery",
            "message": "Started researching the target market and constraints.",
        },
    )
    assert trace_response.status_code == 201, trace_response.text
    trace = trace_response.json()
    assert trace["event"] == "research_started"
    assert trace["stage"] == "idea_discovery"

    list_response = client.get(f"/projects/{project_id}/traces")
    assert list_response.status_code == 200, list_response.text
    events = list_response.json()
    assert len(events) >= 1
    assert events[0]["event"] == "research_started"
