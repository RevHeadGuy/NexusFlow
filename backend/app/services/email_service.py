"""Outbound email delivery.

A small, dependency-free mailer built on the standard library ``smtplib``. It is
used to send project invitation links. Sending is opt-in: when ``email_enabled``
is false or SMTP is not configured, :func:`send_invitation_email` reports that it
did not send rather than raising, so callers can treat email as best-effort and
always fall back to the copyable invite link.
"""
from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from urllib.parse import quote

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


def build_invite_url(token: str, *, settings: Settings | None = None) -> str:
    """Construct the frontend invitation-accept URL for a raw token.

    Mirrors the link the team page builds in the browser
    (``{origin}/invite?token=...``) but uses the server-configured frontend base
    URL because the backend has no access to ``window.location``.
    """
    settings = settings or get_settings()
    base = settings.frontend_base_url.rstrip("/")
    return f"{base}/invite?token={quote(token)}"


def email_is_configured(settings: Settings | None = None) -> bool:
    """Return True only when email sending is enabled and SMTP host is set."""
    settings = settings or get_settings()
    return bool(settings.email_enabled and settings.smtp_host)


def send_invitation_email(
    *,
    to_email: str,
    invite_url: str,
    project_name: str,
    role: str,
    inviter_name: str | None = None,
    settings: Settings | None = None,
) -> bool:
    """Send a project invitation email. Returns True if a message was sent.

    Never raises on a delivery problem: configuration gaps and SMTP errors are
    logged and reported as ``False`` so the caller can continue (the invitation
    row has already been persisted and the link is still returned to the client).
    """
    settings = settings or get_settings()
    if not email_is_configured(settings):
        logger.info("Email delivery disabled or unconfigured; skipping invitation email to %s.", to_email)
        return False

    inviter = inviter_name or "A teammate"
    message = EmailMessage()
    message["Subject"] = f"You're invited to the {project_name} project on NexusFlow"
    message["From"] = settings.email_from
    message["To"] = to_email
    message.set_content(
        f"{inviter} invited you to join the project \"{project_name}\" on NexusFlow "
        f"as a {role}.\n\n"
        f"Accept the invitation:\n{invite_url}\n\n"
        "This is a single-use link and expires in 7 days. If you did not expect "
        "this invitation, you can ignore this email.\n"
    )

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=settings.smtp_timeout_seconds) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            if settings.smtp_user and settings.smtp_password:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(message)
    except (smtplib.SMTPException, OSError) as exc:
        # Best-effort: the invitation is already created; delivery failure must
        # not break the invite flow.
        logger.warning("Failed to send invitation email to %s: %s", to_email, exc)
        return False

    logger.info("Sent invitation email to %s for project %s.", to_email, project_name)
    return True
