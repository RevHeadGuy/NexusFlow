"""Tests for invitation email delivery and cross-process A2A messaging."""

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.services.email_service import build_invite_url, email_is_configured, send_invitation_email

client = TestClient(app)


def _create_project(name: str) -> str:
    resp = client.post(
        "/projects",
        json={"name": name, "description": "d", "idea": f"Build {name}."},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


# ---------------------------------------------------------------------------
# Email service
# ---------------------------------------------------------------------------


def test_build_invite_url_uses_frontend_base_url():
    settings = Settings(frontend_base_url="https://app.example.com/")
    url = build_invite_url("abc123", settings=settings)
    assert url == "https://app.example.com/invite?token=abc123"


def test_email_not_configured_when_disabled():
    settings = Settings(email_enabled=False, smtp_host="smtp.example.com")
    assert email_is_configured(settings) is False


def test_email_not_configured_without_host():
    settings = Settings(email_enabled=True, smtp_host=None)
    assert email_is_configured(settings) is False


def test_send_invitation_email_noop_when_disabled():
    """With email disabled, send reports False rather than attempting SMTP."""
    settings = Settings(email_enabled=False)
    sent = send_invitation_email(
        to_email="teammate@example.com",
        invite_url="https://app.example.com/invite?token=x",
        project_name="Demo",
        role="editor",
        settings=settings,
    )
    assert sent is False


# ---------------------------------------------------------------------------
# Invitation route surfaces delivery status
# ---------------------------------------------------------------------------


def test_invitation_returns_link_and_email_not_sent_by_default():
    project_id = _create_project("Invite Email Project")
    resp = client.post(
        f"/projects/{project_id}/invitations",
        json={"email": "newcollab@example.com", "role": "reviewer"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    # The raw token is still returned so the link can be shared manually.
    assert body["invite_token"]
    # Email delivery is off by default in the test environment.
    assert body["email_sent"] is False


# ---------------------------------------------------------------------------
# Cross-process A2A: inbound ingest + readable log
# ---------------------------------------------------------------------------


def test_external_agent_message_ingest_and_consume_log():
    project_id = _create_project("A2A Ingest Project")

    ingest = client.post(
        f"/projects/{project_id}/agent-messages",
        json={
            "sender": "external_service",
            "recipient": "architecture_agent",
            "content": "Constraint handed off from an external planning agent.",
            "message_type": "handoff",
        },
    )
    assert ingest.status_code == 201, ingest.text
    created = ingest.json()
    assert created["sender"] == "external_service"
    assert created["recipient"] == "architecture_agent"
    assert created["status"] == "pending"

    # The ingested message appears on the same project A2A log in-process agents read.
    log = client.get(f"/projects/{project_id}/agent-messages")
    assert log.status_code == 200
    ids = [m["id"] for m in log.json()]
    assert created["id"] in ids


def test_external_agent_message_rejects_invalid_type():
    project_id = _create_project("A2A Validation Project")
    resp = client.post(
        f"/projects/{project_id}/agent-messages",
        json={
            "sender": "external_service",
            "recipient": "architecture_agent",
            "content": "x",
            "message_type": "not_a_real_type",
        },
    )
    assert resp.status_code == 422
