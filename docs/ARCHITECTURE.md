# NexusFlow Architecture

## Overview

NexusFlow is a modular multi-agent platform that guides a user from a raw product idea to a researched, evaluated, and implementation-ready technical package. The platform combines a FastAPI backend, a TypeScript frontend, and a durable workflow engine built around explicit state transitions and human approvals.

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
- SQLAlchemy models for projects, workflow runs, decisions, documents, evaluations, and agent events
- PostgreSQL as canonical store; SQLite fallback acceptable for local development and tests
- Explicit versioning and foreign keys to preserve project history

### Agent orchestration
- A Strands-backed Idea Analyst creates a structured idea brief when the Bedrock provider is configured; a mock provider is available for local development.
- A persisted workflow controller tracks stage transitions and human decisions.
- Stage deliverables are reviewable Markdown drafts based on saved project inputs. The research stage creates a plan and does not claim to have searched the web.
- Evaluation reports currently use deterministic rules; they are not model-based evaluations.

### Tooling model
- A separate MCP Streamable HTTP server exposes read-only, project-scoped tools for project context and artifact inspection.
- The local MCP server binds to loopback on port 8001. It does not support external search or project mutations.
- Search, calculation, and GitHub tools remain planned integrations.

### Observability
- Structured logging and OpenTelemetry-inspired spans for workflow events, LLM calls, tool calls, and decisions
- Trace viewer shows sequence, duration, outcome, and relevant metadata
- No secrets are logged

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

The repository is a local prototype with a FastAPI REST API, Next.js workspace, SQLite development persistence, persisted workflow decisions, stage draft generation, versioned artifacts, deterministic evaluation reports, and a local read-only MCP server. It does not yet include A2A, external research, authentication, production migrations, or a deployed multi-agent orchestration service. See `IMPLEMENTATION_PLAN.md` for the current boundaries and follow-up work.
