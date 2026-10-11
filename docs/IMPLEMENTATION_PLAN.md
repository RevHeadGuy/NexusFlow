# NexusFlow Implementation Plan

## Status

This repository is currently a minimal FastAPI starter. The work below resets the implementation plan to a disciplined incremental build, starting with Foundation and the first working project workflow.

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

### Phase 1: Foundation (complete)
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

### Phase 2: First working agent (in progress)
- Idea Analyst agent implementation
- Structured brief schema and persistence
- Real model provider integration with fail-safe configuration
- Frontend project idea form and response display

### Phase 3: Project workflow
- Research + PRD + Architecture execution
- Workflow state transitions and human approval stages
- Resume-from-persisted-state behavior

### Phase 4: Artifacts
- Document editor/viewer
- Version history and export generation
- ZIP packaging for approved artifacts

### Phase 5: Reliability
- Devil's Advocate, consistency check, evaluation engine
- Deterministic validation and test datasets

### Phase 6: Advanced engineering
- MCP tooling and selective parallel research
- Trace viewer and observability improvements
- Agent-specific routing and Redis integration where justified

### Phase 7: Product polish
- Dashboard and responsive UI polish
- Authentication-ready ownership model
- CI, deployment docs, and end-to-end verification

## Milestone Checklist

- [x] Foundation and docs are in place
- [x] Project CRUD backend works
- [x] First LLM-backed agent executes safely in a structured way
- [ ] Approval workflow persists decisions
- [ ] Generated documents are versioned and exportable
- [ ] Evaluations produce review findings
- [ ] Final ZIP package is generated deterministically
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
