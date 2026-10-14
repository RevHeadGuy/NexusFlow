# NexusFlow Architecture and Current Boundaries

## Overview

NexusFlow is a local-first project planning prototype. It guides a user from a software idea through a structured brief, persisted workflow decisions, reviewable stage drafts, and exportable artifacts. The current implementation combines a FastAPI backend, a Next.js frontend, and a local SQLAlchemy database. It is not yet a production multi-agent platform.

## Core architectural principles

1. Human-in-the-loop workflow: no major phase advances without an explicit decision.
2. Durable state: workflow progress, approvals, documents, and artifact versions are persisted before any continuation.
3. Modular backend: business logic sits in services instead of route handlers.
4. Deterministic packaging: generated artifacts are versioned and exported using stable code.
5. Safe agent execution: tools and model integrations are constrained by allowlists and validation.

## Runtime components

### Frontend
- Next.js app shell with left navigation, project dashboard, and workspace views
- Reusable UI building blocks for cards, forms, tables, approval flows, and trace panels
- Client-side typed API integration for projects, documents, and workflow state

### Backend API
- FastAPI application with versioned route modules
- Request validation via Pydantic v2 schemas
- Service layer for project management, workflow controller, and artifact handling

### Persistence
- SQLAlchemy models for projects, workflow state and decisions, artifacts and versions, evaluations, guardrails, traces, and agent runs
- Account records, project memberships, roles, and hashed one-time invitation tokens
- Project-scoped user-curated research sources and version-linked artifact review comments
- Combined workflow/HITL review inbox with stage-specific approval checks and revision-version enforcement
- SQLite is the documented local-development setup; other database URLs may need an additional SQLAlchemy driver and deployment configuration
- Artifacts are versioned, and project relationships are stored through database foreign keys

### AI and workflow processing
- The Idea Analyst creates a structured brief through the mock, Groq, or Amazon Bedrock provider; Groq and Bedrock credentials stay in the backend environment.
- A persisted workflow controller tracks stage transitions and human decisions. Stage drafts are produced from saved project inputs and are not evidence of several autonomous agents collaborating.
- The research stage creates a plan from project inputs and participant-entered sources; it does not search or independently verify external sources.
- Evaluation reports use deterministic rules; they are not model-based evaluations.

### Tooling model
- A separate MCP Streamable HTTP server exposes read-only, project-scoped tools for project context and artifact inspection.
- The local MCP server binds to loopback on port 8001. It does not support external search or project mutations.
- MCP access is denied for projects with multiple members until the MCP transport can identify the signed-in user.
- Search, calculation, and GitHub tools remain planned integrations.

### Observability
- Persisted project trace events, agent-run records, evaluation findings, and workflow decisions can be inspected in the UI
- The traces provide application history; they should not be treated as a complete distributed tracing or production observability system

## Proposed module layout

- backend/app/api/
- backend/app/agents/
- backend/app/orchestration/
- backend/app/tools/
- backend/app/models/
- backend/app/services/
- backend/app/schemas/
- backend/app/evaluations/
- backend/app/observability/
- backend/app/security/
- backend/app/config.py

## Project lifecycle

IDEA SUBMITTED -> IDEA DISCOVERY -> HUMAN APPROVAL -> RESEARCH -> FEASIBILITY -> HUMAN APPROVAL -> PRD/ARCHITECTURE/UX/PLANNING -> CONSISTENCY CHECK -> ADVERSARIAL REVIEW -> QUALITY EVALUATION -> REVISION LOOP -> FINAL APPROVAL -> PACKAGE EXPORT

## Key non-functional requirements

- Clear error handling and safe configuration failures
- Request validation and output schema validation
- Versioned artifacts and restoration-safe project state
- Small deterministic golden evaluation dataset
- CI and test commands that can run without paid provider keys

## Current implementation status

The repository is a local prototype with a FastAPI REST API, Next.js workspace, SQLite development persistence, email/password accounts, project memberships and roles, signed API tokens, persisted workflow templates and decisions, editable versioned artifacts, project briefs, user-curated research sources, review comments, deterministic evaluation reports, and a local read-only MCP server. It does not include A2A, automated external research, account recovery or verification, production migrations, or a deployed multi-agent orchestration service. The MCP server is a local read-only integration, not a public hosted service. See `IMPLEMENTATION_PLAN.md` for current boundaries and follow-up work.
