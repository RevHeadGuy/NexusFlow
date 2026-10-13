from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_idea_analysis_generates_and_persists_brief(monkeypatch):
    project_response = client.post(
        "/projects",
        json={
            "name": "Predictive Maintenance Platform",
            "description": "AI-powered maintenance orchestration.",
            "idea": "Build a predictive maintenance platform for manufacturing.",
        },
    )
    project = project_response.json()
    project_id = project["id"]

    def fake_analyze_idea(idea: str):
        return {
            "problem_statement": "Manufacturing teams lose productivity to unplanned equipment downtime.",
            "target_users": ["plant managers", "maintenance teams", "operations leaders"],
            "goals": ["reduce unplanned downtime", "improve maintenance prioritization"],
            "constraints": ["must work in industrial environments", "requires explainable insights"],
            "success_criteria": ["forecast failure windows with acceptable accuracy", "deliver actionable alerts"],
            "clarifying_questions": ["Which machines are most critical in your fleet?"],
        }

    import app.agents.idea_analyst as idea_analyst_module

    monkeypatch.setattr(idea_analyst_module, "analyze_idea", fake_analyze_idea)

    response = client.post(f"/projects/{project_id}/idea-analysis")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["project_id"] == project_id
    assert payload["problem_statement"]
    assert payload["target_users"][0] == "plant managers"
    assert payload["goals"][0] == "reduce unplanned downtime"

    stored_response = client.get(f"/projects/{project_id}/idea-analysis")
    assert stored_response.status_code == 200
    assert stored_response.json()["project_id"] == project_id
