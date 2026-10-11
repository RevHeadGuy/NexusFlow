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
- Strands execution framework orchestrates specialist agents through graph and workflow patterns.
- Workflow controller tracks stage transitions, status, dependencies, retries, and staleness.
- Execution metadata stays linked to projects and workflow steps for replay and trace inspection.

### Tooling model
- Search, file/document, calc, and GitHub inspection tools behind explicit permission checks
- Tool metadata is recorded and limited to authorized project scopes
- External web content is treated as untrusted input

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

The repository is in the Phase 1 foundation stage. The current milestone includes a health endpoint, config handling, a durable project model, and CRUD routes with tests. The broader multi-agent workflow remains planned and staged for subsequent phases.
