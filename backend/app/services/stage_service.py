"""Create reviewable workflow deliverables from the project's persisted inputs.

These templates are deliberately transparent: they do not claim that external
research or model reasoning took place when no such provider was invoked.
"""

from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.project_brief import ProjectBrief
from app.services.artifact_service import create_artifact, create_artifact_version, list_artifacts
from app.services.evaluation_service import generate_consistency_check, generate_devils_advocate, serialize_report
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
        return ["Research Plan"]

    if stage == "technical_feasibility":
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
