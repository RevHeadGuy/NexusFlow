from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_workflow_starts_and_persists_approval_state():
    project_response = client.post(
        "/projects",
        json={
            "name": "Maintenance Analytics",
            "description": "AI analytics for maintenance operations.",
            "idea": "Build a manufacturing maintenance analytics platform.",
        },
    )
    project = project_response.json()
    project_id = project["id"]

    start_response = client.post(f"/projects/{project_id}/workflow")
    assert start_response.status_code == 200, start_response.text
    workflow = start_response.json()
    assert workflow["project_id"] == project_id
    assert workflow["current_stage"] == "idea_discovery"

    blocked_approval = client.post(
        f"/projects/{project_id}/workflow/decision",
        json={"action": "approve", "stage": "idea_discovery", "notes": "Looks good."},
    )
    assert blocked_approval.status_code == 400
    assert "Idea Brief" in blocked_approval.json()["detail"]

    brief_response = client.post(f"/projects/{project_id}/idea-analysis")
    assert brief_response.status_code == 200, brief_response.text

    prepare_response = client.post(f"/projects/{project_id}/workflow/prepare")
    assert prepare_response.status_code == 200, prepare_response.text

    approval_response = client.post(
        f"/projects/{project_id}/workflow/decision",
        json={"action": "approve", "stage": "idea_discovery", "notes": "Looks good."},
    )
    assert approval_response.status_code == 200, approval_response.text
    decision_payload = approval_response.json()
    assert decision_payload["decision"] == "approve"

    read_response = client.get(f"/projects/{project_id}/workflow")
    assert read_response.status_code == 200
    assert read_response.json()["current_stage"] == "market_research"
    assert read_response.json()["status"] == "in_progress"


def test_workflow_resume_reuses_persisted_state():
    project_response = client.post(
        "/projects",
        json={
            "name": "Asset Health Monitor",
            "description": "Asset health insights.",
            "idea": "Build an asset health monitoring product for industrial plants.",
        },
    )
    project_id = project_response.json()["id"]

    client.post(f"/projects/{project_id}/workflow")
    client.post(
        f"/projects/{project_id}/workflow/decision",
        json={"action": "request_changes", "stage": "idea_discovery", "notes": "Need clearer target users."},
    )

    resumed = client.get(f"/projects/{project_id}/workflow")
    assert resumed.status_code == 200
    assert resumed.json()["status"] == "revision_requested"
    assert resumed.json()["current_stage"] == "idea_discovery"
