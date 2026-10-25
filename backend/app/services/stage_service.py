"""Create reviewable workflow deliverables from the project's persisted inputs.

These templates are deliberately transparent: they do not claim that external
research or model reasoning took place when no such provider was invoked.
"""

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.project import Project
from app.models.project_brief import ProjectBrief
from app.services.artifact_service import create_artifact, create_artifact_version, list_artifacts
from app.services.evaluation_service import generate_consistency_check, generate_devils_advocate, serialize_report
from app.services.orchestrator_service import GuardrailBlocked, run_agent_stage
from app.services.research_service import list_research_sources


def _save_markdown(db: Session, project_id: str, name: str, content: str):
    existing = next((artifact for artifact in list_artifacts(db, project_id) if artifact.name == name), None)
    if existing is None:
        return create_artifact(db, project_id, name, "markdown", content)
    # Preparing a stage again must not silently replace a reviewer's saved edits.
    # Regeneration can be added later as an explicit action with a clear version entry.
    return existing


def _brief_markdown(project: Project, brief: ProjectBrief) -> str:
    sections = [
        ("Problem statement", brief.problem_statement),
        ("Target users", "\n".join(f"- {item}" for item in brief.target_users)),
        ("Goals", "\n".join(f"- {item}" for item in brief.goals)),
        ("Constraints", "\n".join(f"- {item}" for item in brief.constraints)),
        ("Success criteria", "\n".join(f"- {item}" for item in brief.success_criteria)),
    ]
    body = "\n\n".join(f"## {title}\n\n{value}" for title, value in sections)
    if brief.clarifying_questions:
        body += "\n\n## Open questions\n\n" + "\n".join(f"- {item}" for item in brief.clarifying_questions)
    return f"# {project.name}: Idea Brief\n\n{body}\n"


def _research_plan_markdown(db: Session, project: Project) -> str:
    sources = list_research_sources(db, project.id)
    evidence_sections = []
    for index, source in enumerate(sources, start=1):
        notes = f"- Notes: {source.notes}\n" if source.notes else ""
        reviewed = "Reviewed by a project participant" if source.reviewed else "Not reviewed"
        evidence_sections.append(
            f"### [{index}] {source.title}\n\n"
            f"- URL: {source.url}\n"
            f"- Finding: {source.finding}\n"
            f"- Review status: {reviewed}\n"
            f"- Added by: {source.added_by}\n"
            f"{notes}"
        )
    evidence = "\n\n".join(evidence_sections) or (
        "No sources recorded yet. Add source-backed findings before treating market assumptions as validated."
    )
    return f"""# Research Plan: {project.name}

> This is a user-curated evidence log, not automated external research. NexusFlow does not fetch or independently verify these sources.

## Product concept
{project.idea.strip()}

## Questions to investigate
- Who experiences this problem, and how do they solve it today?
- Which alternatives are used, and what are their trade-offs?
- What evidence would validate willingness to adopt or pay?
- Which market, policy, or operational sources should be checked?

## Evidence log
{evidence}
"""


def refresh_research_plan(db: Session, project: Project):
    """Explicitly create a new plan version using the saved source log."""
    content = _research_plan_markdown(db, project)
    existing = next((item for item in list_artifacts(db, project.id) if item.name == "Research Plan"), None)
    if existing is None:
        return create_artifact(db, project.id, "Research Plan", "markdown", content)
    create_artifact_version(db, existing.id, content, "Updated from project research sources")
    return existing


def sync_idea_brief_artifact(db: Session, project: Project, brief: ProjectBrief) -> None:
    """Keep an already-prepared idea brief artifact in sync with reviewer edits."""
    existing = next((item for item in list_artifacts(db, project.id) if item.name == "Idea Brief"), None)
    if existing is not None:
        content = _brief_markdown(project, brief)
        if existing.content != content:
            create_artifact_version(db, existing.id, content, "Updated from the saved project brief")


def _agents_enabled() -> bool:
    """Agent generation runs only with a live provider.

    On the mock provider (default local/CI), stages fall back to the transparent
    deterministic templates so the app stays runnable without credentials and does
    not imply reasoning that did not happen.
    """
    return get_settings().llm_provider.lower() != "mock"


def _project_context(project: Project, brief: ProjectBrief | None) -> str:
    """Build a compact context string shared across stage agents."""
    lines = [
        f"Project name: {project.name}",
        f"Description: {project.description or 'Not provided.'}",
        f"Idea: {project.idea.strip()}",
    ]
    if brief is not None:
        lines += [
            "",
            "Structured brief:",
            f"- Problem: {brief.problem_statement}",
            f"- Target users: {', '.join(brief.target_users)}",
            f"- Goals: {', '.join(brief.goals)}",
            f"- Constraints: {', '.join(brief.constraints)}",
            f"- Success criteria: {', '.join(brief.success_criteria)}",
        ]
    return "\n".join(lines)


def _run_stage_agent(
    db: Session,
    project: Project,
    stage: str,
    agent,
    prompt: str,
    *,
    tool_artifacts: list[str] | None = None,
    handoff_to: str | None = None,
) -> dict | None:
    """Run a stage agent, returning its structured output or None to fall back.

    A guardrail block is treated as a hard failure (re-raised) because the output
    is unsafe to persist. Any other agent/provider error falls back to the
    deterministic template so a stage can still be prepared.

    ``tool_artifacts`` (Phase C) names prior artifacts the agent reads via project
    tools; ``handoff_to`` (Phase D) names a downstream agent to notify on success.
    """
    try:
        result = run_agent_stage(
            db,
            project_id=project.id,
            stage=stage,
            agent=agent,
            user_prompt=prompt,
            scope_idea=project.idea,
            tool_artifacts=tool_artifacts,
            handoff_to=handoff_to,
        )
        return result.output
    except GuardrailBlocked:
        raise
    except Exception:  # noqa: BLE001 — provider/transport failure: fall back to template
        return None


def prepare_stage_deliverables(db: Session, project: Project, stage: str) -> list[str]:
    brief = db.query(ProjectBrief).filter(ProjectBrief.project_id == project.id).first()
    idea = project.idea.strip()
    description = project.description or "Not provided."
    names: list[str] = []

    if stage == "idea_discovery":
        if brief is None:
            raise ValueError("Analyze the idea first to create the project brief.")
        _save_markdown(db, project.id, "Idea Brief", _brief_markdown(project, brief))
        return ["Idea Brief"]

    if stage == "market_research":
        _save_markdown(db, project.id, "Research Plan", _research_plan_markdown(db, project))
        if _agents_enabled():
            from app.agents.market_research import MarketResearchAgent, render_market_research

            output = _run_stage_agent(
                db, project, stage, MarketResearchAgent(),
                _project_context(project, brief) + "\n\nAnalyze the market for this product.",
                handoff_to="technical_feasibility",
            )
            if output is not None:
                _save_markdown(db, project.id, "Market Analysis", render_market_research(project.name, output))
                return ["Research Plan", "Market Analysis"]
        return ["Research Plan"]

    if stage == "technical_feasibility":
        if _agents_enabled():
            from app.agents.technical_feasibility import TechnicalFeasibilityAgent, render_technical_feasibility

            output = _run_stage_agent(
                db, project, stage, TechnicalFeasibilityAgent(),
                _project_context(project, brief) + "\n\nAssess the technical feasibility of building this product.",
                handoff_to="architecture_agent",
            )
            if output is not None:
                _save_markdown(db, project.id, "Technical Feasibility", render_technical_feasibility(project.name, output))
                return ["Technical Feasibility"]
        content = f"""# Technical Feasibility: {project.name}

> Initial planning draft based on the submitted idea. Validate choices against real requirements and constraints.

## Concept
{idea}

## Initial system areas
- User-facing application and project workspace
- API and durable data store
- Identity, authorization, and audit trail
- External integrations and background work, if required by validated scope

## Decisions still needed
- Expected users, traffic, latency, availability, and data retention
- Sensitive data categories and access boundaries
- Required integrations and their authentication model
- Deployment environment, operations owner, and recovery objectives

## Feasibility status
Not independently validated. Confirm these assumptions with engineering and security owners before committing to an implementation plan.
"""
        _save_markdown(db, project.id, "Technical Feasibility", content)
        return ["Technical Feasibility"]

    if stage == "prd_architecture":
        if _agents_enabled():
            from app.agents.architecture_agent import ArchitectureAgent, render_architecture
            from app.agents.prd_agent import PrdAgent, render_prd

            context = _project_context(project, brief)
            prd_output = _run_stage_agent(
                db, project, stage, PrdAgent(),
                context + "\n\nWrite the product requirements document for this product.",
            )
            if prd_output is not None:
                _save_markdown(db, project.id, "Product Requirements", render_prd(project.name, prd_output))
            # Phase C + D: the architecture agent reads the PRD and feasibility
            # artifacts via project tools, and consumes any handoff from the
            # feasibility agent, so its design is grounded in prior stages.
            arch_output = _run_stage_agent(
                db, project, stage, ArchitectureAgent(),
                context + "\n\nDraft the system architecture outline for this product.",
                tool_artifacts=["Product Requirements", "Technical Feasibility"],
            )
            if arch_output is not None:
                _save_markdown(db, project.id, "Architecture Outline", render_architecture(project.name, arch_output))
            # If both agents produced output, the stage is complete via agents.
            if prd_output is not None and arch_output is not None:
                return ["Product Requirements", "Architecture Outline"]
            # Otherwise fall through to fill any missing artifact with the template
            # (_save_markdown is non-destructive, so agent output is preserved).
        prd = f"""# Product Requirements: {project.name}

## Summary
{description}

## Problem and intended users
{brief.problem_statement if brief else idea}

## Goals
{chr(10).join(f'- {item}' for item in brief.goals) if brief else '- Confirm measurable product goals with the project owner.'}

## Success criteria
{chr(10).join(f'- {item}' for item in brief.success_criteria) if brief else '- Define measurable acceptance criteria before implementation.'}

## Open questions
{chr(10).join(f'- {item}' for item in (brief.clarifying_questions if brief else [])) or '- Confirm user needs, constraints, and measurable outcomes.'}
"""
        architecture = f"""# Architecture Outline: {project.name}

## Scope
{idea}

## Proposed boundaries
- Web client for user workflows and review
- API layer for validation and domain operations
- Persistent store for projects, decisions, and versioned artifacts
- Background agent/tool execution behind explicit permissions

## Quality requirements to define
- Authentication and project-level authorization
- Auditability and data retention
- Reliability, latency, and recovery targets
- Integration permissions and secret handling

> This is a starting outline, not a validated architecture. Confirm requirements before selecting production technologies.
"""
        _save_markdown(db, project.id, "Product Requirements", prd)
        _save_markdown(db, project.id, "Architecture Outline", architecture)
        return ["Product Requirements", "Architecture Outline"]

    if stage == "quality_review":
        if _agents_enabled():
            from app.agents.quality_evaluator import QualityEvaluatorAgent, render_quality_review

            artifact_summaries = "\n".join(
                f"- {item.name}: {(item.content or '')[:400]}" for item in list_artifacts(db, project.id)
            )
            output = _run_stage_agent(
                db, project, stage, QualityEvaluatorAgent(),
                _project_context(project, brief)
                + "\n\nProject artifacts to review:\n" + (artifact_summaries or "None prepared yet.")
                + "\n\nReview the project for gaps, inconsistencies, and unsupported claims.",
            )
            if output is not None:
                _save_markdown(db, project.id, "Agent Quality Review", render_quality_review(project.name, output))
        reports = [
            generate_consistency_check(db, project.id, project.idea, project.description),
            generate_devils_advocate(db, project.id, project.idea, project.description),
        ]
        serialized = [serialize_report(db, report) for report in reports]
        sections = []
        for report in serialized:
            findings = "\n".join(
                f"### [{item['severity'].upper()}] {item['title']}\n\n{item['description']}\n\n"
                f"**Evidence:** {item.get('evidence') or 'None recorded'}\n\n"
                f"**Recommendation:** {item.get('recommendation') or 'No recommendation recorded'}"
                for item in report["findings"]
            )
            sections.append(f"## {report['report_type'].replace('_', ' ').title()}\n\n{findings}")
        _save_markdown(db, project.id, "Quality Review", "# Quality Review\n\n" + "\n\n".join(sections))
        return ["Quality Review"]

    if stage == "final_approval":
        artifact_names = [item.name for item in list_artifacts(db, project.id) if item.name != "Final Package Guide"]
        content = f"""# Final Package Guide: {project.name}

## Project
{description}

## Package contents
{chr(10).join(f'- {name}' for name in artifact_names) or '- No workflow artifacts have been prepared yet.'}

## Approval
This guide lists the latest saved artifacts. Review and approve them in NexusFlow before sharing or implementing.
"""
        _save_markdown(db, project.id, "Final Package Guide", content)
        return ["Final Package Guide"]

    raise ValueError(f"Unsupported workflow stage: {stage}")
