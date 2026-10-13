from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["application"] == "NexusFlow"


def test_create_and_list_projects():
    payload = {
        "name": "Predictive Maintenance Platform",
        "description": "AI-powered maintenance orchestration for manufacturing lines.",
        "idea": "Build a predictive maintenance platform for manufacturing.",
    }

    create_response = client.post("/projects", json=payload)

    assert create_response.status_code == 201, create_response.text
    created = create_response.json()
    assert created["name"] == payload["name"]
    assert created["idea"] == payload["idea"]
    assert created["description"] == payload["description"]
    assert "id" in created

    list_response = client.get("/projects")

    assert list_response.status_code == 200
    project_ids = [project["id"] for project in list_response.json()]
    assert created["id"] in project_ids
