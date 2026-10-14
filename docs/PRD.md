# NexusFlow Product Requirements Document

> **This document is product direction, not a claim that every requirement ships today.** For implemented capabilities and limitations, see [ARCHITECTURE.md](ARCHITECTURE.md) and [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md).

## Product summary

NexusFlow aims to help founders and product teams turn an initial software idea into a structured, human-reviewable project plan while retaining control over decisions. The current prototype supports project briefs, workflow drafts, approvals, artifact review, deterministic evaluations, and export. External research and a collaborating multi-agent system remain future goals.

## Target users

- Founders with an early concept and limited decision support
- Product teams validating technical feasibility and product scope
- Engineering managers preparing implementation roadmaps
- Organizations needing traceable, reviewable AI-generated project artifacts

## Problem statement

Teams often collect good ideas but struggle to turn them into well-scoped products. AI-generated outputs can be inconsistent or unsupported. NexusFlow is intended to address that by combining structured project context, explicit human review, and deterministic document packaging. The current implementation does not yet provide collaborating specialist agents or sourced external research.

## Intended user journeys

The following describe the product direction. Current stage generation is draft-oriented and should not be interpreted as external research or autonomous multi-agent execution.

1. User creates a new project from an initial idea.
2. The system asks clarifying questions if needed.
3. Research and technical analysis are generated and reviewed.
4. The user approves or requests changes at each decision gate.
5. Final documents are assembled and exported as a package.

## Functional requirements

- Create, list, retrieve, update, and delete projects
- Register and sign in; control project access through owner, editor, reviewer, and viewer roles
- Invite a collaborator by email using a revocable, expiring, single-use link
- Attribute workflow decisions and review actions to the authenticated account
- Submit a raw idea and capture clarifying questions
- Persist project state and resume workflow progress after restart
- Generate research and specification artifacts per project stage
- Route to human approval and revision flows
- Display document previews and downloadable exports
- Produce evaluation findings with evidence and severity
- Exports final project package as a ZIP

## Non-functional requirements

- Real backend persistence and workflow state
- Explicit approval before continuation
- Validation of model outputs against schemas
- Safe tool use and least-privilege authorization
- Clear configuration errors when providers or database settings are missing

## Success metrics

- Projects move through structured workflow stages without silent data loss
- Human approval decisions persist across restarts
- Generated project packages include all required artifacts
- Evaluation process produces reviewable findings with evidence

## Constraints

- No fabricated benchmark claims
- No live model calls in default CI process
- No reliance on in-memory approval state alone
- No destructive shell or GitHub operations by default

## Out of scope for Phase 1

- Full multi-agent end-to-end product workflow
- Advanced MCP tool orchestration
- Final UI polish and advanced dashboard features

## Planned future phases

The product roadmap expands to research, architecture, UX, evaluation, approvals, packaging, and higher-end observability capabilities after the foundational backend and workflow scaffolding are complete.
