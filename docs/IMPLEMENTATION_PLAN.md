# NexusFlow Implementation Plan

## Status

This repository has a local full-stack prototype: project CRUD, a structured idea brief, persisted workflow decisions, reviewable stage drafts, versioned artifacts, deterministic evaluations, and a read-only MCP server. This plan distinguishes those working foundations from integrations that are still needed for production use.

## Goals

- Deliver a production-oriented multi-agent engineering platform for turning raw ideas into researched, validated project specifications.
- Keep the system modular and auditable.
- Validate each milestone with real tests before moving to the next phase.

## Architecture Summary

### Frontend
- Next.js App Router
- TypeScript, Tailwind CSS, shadcn/ui, Lucide icons
- Dashboard, project workspace, workflow, document viewer, approval controls

### Backend
- FastAPI + Pydantic v2
- SQLAlchemy 2 + PostgreSQL as canonical persistence layer
- Strands agent orchestration for workflow execution
- Modular services for projects, workflow, artifacts, evaluations, and approval logic

### Supporting Services
- Redis optional for caching/job coordination
- Docker Compose for local stack
- OpenTelemetry-compatible tracing and structured logging

## Phase roadmap

### Foundation (implemented for local development)
- Repository and documentation alignment
- Backend configuration and environment handling
- Health endpoint and startup readiness
- Database session management and basic project CRUD
- Initial backend tests covering health and project creation/retrieval

Acceptance criteria:
- Health endpoint responds successfully
- Project create/list/get endpoints function
- Data persists in a local transactional session
- Tests pass without depending on live LLM access

### Idea discovery (implemented with a provider boundary)
- Idea Analyst agent implementation
- Structured brief schema and persistence
- Real model provider integration with fail-safe configuration
- Frontend project idea form and response display

### Workflow and deliverables (prototype implemented)
- Persisted stage transitions and human decisions
- Versioned Markdown drafts for research planning, feasibility, PRD, architecture, quality review, and final package guide
- Research is a plan only; external source discovery and citation are future work

### Artifacts (partially implemented)
- Document editor/viewer
- Version history and export generation
- ZIP packaging for approved artifacts

### Reliability (partially implemented)
- Devil's Advocate, consistency check, evaluation engine
- Deterministic validation and test datasets

### MCP tooling (local, read-only implementation)
- Streamable HTTP MCP endpoint for project context and artifacts
- Mutating tools and external MCP server connections are not enabled
- A2A is not implemented; revisit when independent agents need cross-service task handoff

### Frontend delivery (separate from backend roadmap)
- Next.js app shell and dashboard UI
- Authentication-ready ownership model
- CI, deployment docs, and end-to-end verification

## Milestone Checklist

- [x] Foundation and docs are in place
- [x] Project CRUD backend works
- [x] First LLM-backed agent executes safely in a structured way
- [x] Approval workflow persists decisions
- [x] Generated stage drafts are versioned and exportable
- [x] Deterministic evaluations produce review findings
- [x] MCP exposes read-only project and artifact tools
- [x] Project artifact ZIP package is generated deterministically
- [ ] Frontend and backend pass CI checks

## Risk Notes

- Strands SDK interfaces must be validated against the installed package rather than guessed.
- Postgres should be the canonical production store, but local development may fall back to a lightweight SQLite configuration when no database is configured.
- Human approval must be stored explicitly before workflow continuation.

## Implementation Rules

- Preserve and extend useful existing files.
- Avoid fake/mock-only flows that do not actually persist or validate state.
- Keep modules small, typed, and testable.
- Maintain a clear distinction between implemented, partially implemented, and planned work.
