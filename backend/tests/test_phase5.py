from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_reliability_evaluation_generates_findings():
    project_response = client.post(
        "/projects",
        json={
            "name": "CareFlow",
            "description": "Workflow tooling for care teams.",
            "idea": "Build a healthcare workflow system for care coordination across clinics, nurses, and physicians.",
        },
    )
    assert project_response.status_code == 201, project_response.text
    project_id = project_response.json()["id"]

    consistency_response = client.post(f"/projects/{project_id}/evaluations/consistency-check")
    assert consistency_response.status_code == 200, consistency_response.text
    consistency = consistency_response.json()
    assert consistency["report_type"] == "consistency_check"
    assert "findings" in consistency
    assert isinstance(consistency["findings"], list)
    assert len(consistency["findings"]) >= 1
    assert consistency["findings"][0]["severity"] in {"info", "warning", "critical"}

    devil_response = client.post(f"/projects/{project_id}/evaluations/devils-advocate")
    assert devil_response.status_code == 200, devil_response.text
    devil = devil_response.json()
    assert devil["report_type"] == "devils_advocate"
    assert "findings" in devil
    assert len(devil["findings"]) >= 1

    list_response = client.get(f"/projects/{project_id}/evaluations")
    assert list_response.status_code == 200, list_response.text
    reports = list_response.json()
    assert len(reports) >= 2
