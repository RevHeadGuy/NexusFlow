# NexusFlow Deployment and Hardening Guide

> **Read this before exposing NexusFlow to anything beyond your own machine.**
> The default configuration is a local-first prototype. It is not safe to put on
> the public internet as-is. This guide lists what to change and verify first.

NexusFlow ships intentionally permissive defaults for a fast local start (a mock
LLM provider, SQLite, tokens in browser storage, no email). Moving to a shared or
internet-facing deployment means replacing those defaults with hardened choices.
Work through the checklist below; each item links to the setting or component it
concerns.

## Architecture recap

```text
Browser ── HTTPS ──> reverse proxy (TLS) ──> Next.js frontend (3000)
                                        └──> FastAPI backend (8000)
                                                   └──> database (Postgres recommended)
```

In production you should terminate TLS at a reverse proxy (nginx, Caddy, a cloud
load balancer) and never expose the raw backend or the MCP server to the public
internet.

## Pre-deployment hardening checklist

Treat every unchecked box as a blocker.

### Secrets and identity
- [ ] Set a stable, high-entropy `AUTH_SECRET_KEY`. If omitted, a random key is
      generated per process: restarts invalidate all tokens and multiple workers
      will not share sessions. Generate one with
      `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
- [ ] Shorten `AUTH_TOKEN_EXPIRE_MINUTES` from the 720 (12h) default to match your
      risk tolerance.
- [ ] Keep all provider credentials (`GROQ_API_KEY`, AWS keys) in the backend
      process environment only. Never commit them; never put them in any
      `NEXT_PUBLIC_*` variable.
- [ ] Rotate any credential that was ever committed or shared.

### Transport and network
- [ ] Terminate TLS at a reverse proxy; do not serve plain HTTP.
- [ ] Bind the backend to a private interface and front it with the proxy. Do not
      publish port 8000 or 8001 directly.
- [ ] Keep the local MCP server (`app.mcp_server`, port 8001) on loopback only. It
      has no authentication and refuses multi-member projects by design — it is a
      local developer integration, not a production service.
- [ ] Set `CORS_ORIGINS` to the exact frontend origin(s). Remember CORS is not
      authentication; it does not stop non-browser clients.

### Data and persistence
- [ ] Use PostgreSQL rather than SQLite for any shared deployment. Point
      `DATABASE_URL` at it (e.g. `postgresql+psycopg://user:pass@host:5432/nexusflow`)
      and install the matching driver.
- [ ] Apply schema with Alembic migrations (`alembic upgrade head`) rather than
      relying on startup table creation. See [backend/migrations/README.md](../backend/migrations/README.md).
- [ ] Put a backup and restore process in place for the database.

### Sessions and accounts
- [ ] Understand the current session model: the frontend stores the bearer token
      in browser local storage. For an internet-facing service, move to a
      secure, HttpOnly cookie/session design and add CSRF protection.
- [ ] Add the account-lifecycle features that are not implemented yet before
      onboarding real users: email verification, password reset/recovery, login
      rate limiting, and server-side session revocation.

### Email
- [ ] To send invitation emails, set `EMAIL_ENABLED=true`, configure the SMTP
      values, and set `FRONTEND_BASE_URL` to the public frontend URL so links
      resolve. When disabled, invitations still work — the link is returned for
      manual sharing. See the invitation flow in `backend/app/api/members.py` and
      `backend/app/services/email_service.py`.

### Agent-to-agent (A2A) delivery
- [ ] The in-process A2A bus needs no configuration. Only enable cross-process
      delivery (`A2A_EXTERNAL_DELIVERY_ENABLED=true` with `A2A_WEBHOOK_URL`) when a
      trusted external agent service is meant to receive handoffs. Set
      `A2A_WEBHOOK_TOKEN` and verify the endpoint is authenticated and over TLS.
      The inbound ingest route (`POST /projects/{id}/agent-messages`) is subject
      to the usual project membership and role checks — do not bypass them.

### Observability and operations
- [ ] Set `DEBUG=false` and `APP_ENV=production`.
- [ ] Configure structured logging and ship logs off-host.
- [ ] Add a health check against `GET /health` to your orchestrator.
- [ ] Run the backend under a process manager (systemd, a container, or a
      platform runtime) with multiple workers behind the proxy.

## Running with Docker (reference)

NexusFlow does not yet ship an official image. A minimal production shape:

- Backend: a Python image that installs `backend/requirements.txt`, runs
  `alembic upgrade head`, then serves `uvicorn app.main:app` behind the proxy.
- Frontend: a Node image that runs `npm ci && npm run build` and serves
  `npm run start`, with `NEXT_PUBLIC_API_URL` pointing at the public backend URL.
- Database: a managed PostgreSQL instance or a `postgres` container with a
  persistent volume.

Keep secrets out of images; inject them as runtime environment variables.

## Configuration reference

All backend settings are read from the process environment or `backend/.env`.
See [.env.example](../.env.example) for a copyable template and the table in the
[README](../README.md#configuration-reference) for the full list, including the
email and A2A settings described above.

## What is still missing for production

These are known gaps, not oversights in this guide:

- Account verification, password recovery, and login rate limiting
- Secure, server-side session handling (currently local-storage bearer tokens)
- An official Docker/Compose setup and infrastructure-as-code
- Automated database backups and a tested restore runbook
- End-to-end monitoring, alerting, and tracing wired to a backend

Until these land, run NexusFlow only on trusted networks with non-sensitive data.
