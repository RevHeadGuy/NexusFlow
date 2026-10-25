# NexusFlow Architecture and Current Boundaries

## Overview

NexusFlow is a local-first project planning prototype. It guides a user from a software idea through a structured brief, persisted workflow decisions, agent-generated and reviewable stage deliverables, and exportable artifacts. The current implementation combines a FastAPI backend, a Next.js frontend, and a local SQLAlchemy database. Stage generation is handled by a pipeline of specialized agents that share a provider abstraction, guardrail chain, and run-tracking lifecycle, with human review gating every advance. It remains a local prototype rather than a hardened, deployed platform.

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
- SQLAlchemy models for projects, workflow state and decisions, artifacts and versions, evaluations, guardrails, traces, agent runs, and agent-to-agent messages
- Account records, project memberships, roles, and hashed one-time invitation tokens
- Project-scoped user-curated research sources and version-linked artifact review comments
- Combined workflow/HITL review inbox with stage-specific approval checks and revision-version enforcement
- SQLite is the documented local-development setup; other database URLs may need an additional SQLAlchemy driver and deployment configuration
- Artifacts are versioned, and project relationships are stored through database foreign keys

### AI and workflow processing
- A pipeline of specialized agents backs the workflow: idea analysis, market research, technical feasibility, PRD, architecture, and quality evaluation. Each subclasses a shared `BaseAgent` and talks to the configured provider through a common abstraction (`app/agents/providers.py`): mock, Groq, or Amazon Bedrock. Groq and Bedrock credentials stay in the backend environment.
- Every agent runs through one orchestration lifecycle (`app/services/orchestrator_service.py`): start a run record, call the agent, run the guardrail chain, persist violations, read prior artifacts through the tool layer, optionally hand off to a downstream agent, and record traces. Output is persisted only if it passes guardrails.
- A persisted workflow controller tracks stage transitions and human decisions; no stage advances without an explicit human decision.
- Agent generation runs only with a live provider. On the mock provider (default local/CI), agent-backed stages fall back to transparent deterministic templates so a credential-free run does not imply model reasoning that did not happen.
- The research stage creates a plan from project inputs and participant-entered sources; agents do not search or independently verify external sources.
- The consistency and Devil's Advocate reports use deterministic rules; the Quality Evaluator agent adds a complementary model-based review when a live provider is configured.

### Tooling model
- A shared backend tool layer (`app/agents/tools.py`) implements read-only, project-scoped access to project context and artifacts. It is the single source of truth used in two ways: agents call it in-process to ground their output in prior deliverables, and the MCP server wraps it over Streamable HTTP for external clients.
- A separate MCP Streamable HTTP server exposes those same three read-only tools. It binds to loopback on port 8001 and does not support external search or project mutations.
- MCP access is denied for projects with multiple members until the MCP transport can identify the signed-in user. The in-process agent path has no such restriction because it runs inside the authenticated request lifecycle.
- Search, calculation, and GitHub tools, and connections to external MCP servers, remain planned integrations.

### Agent-to-agent (A2A) messaging
- Agents communicate within a single project through a persisted message bus (`agent_messages` table, `app/services/agent_message_service.py`). An earlier stage posts a message addressed to a later agent, which consumes it on its next run and folds it into its prompt.
- The default handoff chain is `market_research → technical_feasibility → architecture_agent`. Handoffs are recorded as project traces and are readable through `GET /projects/{id}/agent-messages`.
- This bus is internal and in-process within one project; it is not a cross-service or cross-network agent protocol.

### Observability
- Persisted project trace events, agent-run records, evaluation findings, and workflow decisions can be inspected in the UI
- The traces provide application history; they should not be treated as a complete distributed tracing or production observability system

## Module layout

- backend/app/api/ — REST route modules
- backend/app/agents/ — provider abstraction (`providers.py`), shared `BaseAgent` (`base.py`), per-stage agents, and the read-only project tool layer (`tools.py`)
- backend/app/guardrails/ — guardrail base types, registry, and validators
- backend/app/models/ — SQLAlchemy models (including `agent_message.py`)
- backend/app/services/ — business logic, including `orchestrator_service.py` (agent run lifecycle) and `agent_message_service.py` (A2A bus)
- backend/app/schemas/ — Pydantic request/response models
- backend/app/mcp_server.py — local read-only MCP server wrapping the shared tool layer
- backend/app/security.py — authentication and project-access middleware
- backend/app/config.py — settings

## Project lifecycle

IDEA SUBMITTED -> IDEA DISCOVERY -> HUMAN APPROVAL -> RESEARCH -> FEASIBILITY -> HUMAN APPROVAL -> PRD/ARCHITECTURE/UX/PLANNING -> CONSISTENCY CHECK -> ADVERSARIAL REVIEW -> QUALITY EVALUATION -> REVISION LOOP -> FINAL APPROVAL -> PACKAGE EXPORT

## Key non-functional requirements

- Clear error handling and safe configuration failures
- Request validation and output schema validation
- Versioned artifacts and restoration-safe project state
- Small deterministic golden evaluation dataset
- CI and test commands that can run without paid provider keys

## Current implementation status

The repository is a local prototype with a FastAPI REST API, Next.js workspace, SQLite development persistence, email/password accounts, project memberships and roles, signed API tokens, persisted workflow templates and decisions, a multi-agent stage-generation pipeline with a shared provider abstraction and orchestration lifecycle, an in-process project tool layer shared with the MCP server, an in-project agent-to-agent message bus, editable versioned artifacts, project briefs, user-curated research sources, review comments, deterministic evaluation reports plus a model-based quality agent, and a local read-only MCP server. It does not include automated external research, account recovery or verification, production migrations, cross-service A2A, or a deployed, hardened orchestration service. The MCP server is a local read-only integration, not a public hosted service. The backend test suite currently predates the authentication layer and needs a login fixture to pass. See `IMPLEMENTATION_PLAN.md` for current boundaries and follow-up work.
