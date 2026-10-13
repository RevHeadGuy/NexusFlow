import io
import zipfile

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_artifact_versioning_and_export():
    project_response = client.post(
        "/projects",
        json={
            "name": "Clinical Insights",
            "description": "AI support for clinical teams.",
            "idea": "Build a clinical insights workspace that summarizes research for medical operations teams.",
        },
    )
    assert project_response.status_code == 201, project_response.text
    project_id = project_response.json()["id"]

    artifact_response = client.post(
        f"/projects/{project_id}/artifacts",
        json={
            "name": "PRD",
            "type": "markdown",
            "content": "# Clinical Insights\n\nThis is the initial product brief.",
        },
    )
    assert artifact_response.status_code == 201, artifact_response.text
    artifact = artifact_response.json()
    assert artifact["name"] == "PRD"
    assert artifact["type"] == "markdown"
    assert artifact["current_version"] == 1

    version_response = client.post(
        f"/projects/{project_id}/artifacts/{artifact['id']}/versions",
        json={
            "content": "# Clinical Insights\n\nThis is the revised product brief.",
            "summary": "Refined product narrative.",
        },
    )
    assert version_response.status_code == 201, version_response.text
    version_payload = version_response.json()
    assert version_payload["version"] == 2
    assert version_payload["summary"] == "Refined product narrative."

    export_response = client.get(f"/projects/{project_id}/artifacts/{artifact['id']}/export")
    assert export_response.status_code == 200, export_response.text
    assert export_response.headers["content-type"].startswith("application/zip")

    with zipfile.ZipFile(io.BytesIO(export_response.content)) as archive:
        names = archive.namelist()
        assert names
        assert any(name.endswith("PRD.md") or name.endswith("artifact.md") for name in names)
