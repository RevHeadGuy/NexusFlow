"""Agent orchestration.

Runs a model-backed agent through the full NexusFlow run lifecycle:

    start_run -> agent.run -> run_guardrails -> persist_violations
              -> complete_run / fail_run -> trace

This generalizes the hand-written flow in ``api/projects.py`` so every stage
agent executes with the same tracking, guardrails, and auditing. It raises
:class:`GuardrailBlocked` when the agent output has a HIGH/CRITICAL violation so
callers can surface a clean error and avoid persisting unsafe output.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.tools import ProjectToolbox
from app.guardrails import run_guardrails
from app.services.agent_message_service import consume_pending_for, send_message
from app.services.guardrail_service import persist_violations
from app.services.mlops_service import complete_run, fail_run, start_run
from app.services.trace_service import create_trace


class GuardrailBlocked(Exception):
    """Raised when agent output is blocked by a HIGH/CRITICAL guardrail violation."""

    def __init__(self, agent_name: str, messages: list[str]) -> None:
        self.agent_name = agent_name
        self.messages = messages
        super().__init__(f"Agent '{agent_name}' output blocked by guardrails.")


@dataclass
class AgentRunResult:
    output: dict[str, object]
    usage: dict[str, object] | None
    run_id: str
    agent_name: str


def run_agent_stage(
    db: Session,
    *,
    project_id: str,
    stage: str,
    agent: BaseAgent,
    user_prompt: str,
    scope_idea: str = "",
    tool_artifacts: list[str] | None = None,
    handoff_to: str | None = None,
    handoff_summary: str | None = None,
) -> AgentRunResult:
    """Execute one agent with full tracking, tools, A2A, and guardrails.

    Parameters
    ----------
    stage:
        Workflow stage key recorded on the AgentRun and guardrail records.
    agent:
        A ``BaseAgent`` instance (its ``agent_name`` drives guardrail/schema lookup).
    user_prompt:
        The prompt text handed to the agent.
    scope_idea:
        Original idea text used by the scope guardrail; usually ``project.idea``.
    tool_artifacts:
        Phase C — names of prior artifacts the agent should read via the project
        toolbox and have folded into its prompt as grounding context.
    handoff_to:
        Phase D — if set, after a successful run the agent posts an A2A message to
        this recipient agent so a later stage can pick it up.
    handoff_summary:
        Optional explicit content for the handoff message; defaults to a short
        summary of this agent's output.
    """
    # Phase C: ground the prompt in prior deliverables through the shared toolbox.
    augmented_prompt = user_prompt
    if tool_artifacts:
        toolbox = ProjectToolbox(db, project_id)
        gathered = toolbox.gather_prior_artifacts(tool_artifacts)
        if gathered:
            context_block = "\n\n".join(
                f"--- {name} (prior artifact) ---\n{content[:1500]}"
                for name, content in gathered.items()
            )
            augmented_prompt = (
                f"{user_prompt}\n\nUse the following prior project artifacts as grounding context:\n\n{context_block}"
            )
            create_trace(
                db,
                project_id,
                event="tool_use",
                stage=stage,
                message=f"{agent.agent_name} read {len(gathered)} prior artifact(s) via project tools.",
                details={"artifacts": list(gathered.keys())},
            )

    # Phase D: fold any pending A2A messages addressed to this agent into the prompt.
    inbox = consume_pending_for(db, project_id, agent.agent_name)
    if inbox:
        messages_block = "\n\n".join(
            f"From {m.sender} ({m.message_type}): {m.content}" for m in inbox
        )
        augmented_prompt = (
            f"{augmented_prompt}\n\nMessages from other agents to consider:\n\n{messages_block}"
        )

    run = start_run(
        db,
        project_id=project_id,
        stage=stage,
        agent_name=agent.agent_name,
        raw_input={"prompt": augmented_prompt},
    )

    try:
        result = agent.run(augmented_prompt, db=db)
    except Exception as exc:  # noqa: BLE001 — recorded and re-raised as a clean error
        fail_run(db, run.id, error_message=str(exc))
        create_trace(
            db,
            project_id,
            event="agent_failed",
            stage=stage,
            message=f"{agent.agent_name} failed: {exc}",
        )
        raise

    guardrail_result = run_guardrails(result.output, agent_name=agent.agent_name, idea=scope_idea)

    if guardrail_result.violations:
        persist_violations(
            db,
            guardrail_result,
            project_id=project_id,
            stage=stage,
            agent_name=agent.agent_name,
            auto_blocked=not guardrail_result.safe_to_proceed,
        )

    usage = result.usage or {}

    if not guardrail_result.safe_to_proceed:
        complete_run(
            db,
            run.id,
            raw_output=result.output,
            input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens"),
            status="guardrail_blocked",
        )
        messages = [v.message for v in guardrail_result.violations]
        create_trace(
            db,
            project_id,
            event="guardrail_blocked",
            stage=stage,
            message=f"{agent.agent_name} output blocked by guardrails.",
            details={"violations": messages},
        )
        raise GuardrailBlocked(agent.agent_name, messages)

    complete_run(
        db,
        run.id,
        raw_output=result.output,
        input_tokens=usage.get("input_tokens"),
        output_tokens=usage.get("output_tokens"),
    )
    create_trace(
        db,
        project_id,
        event="agent_completed",
        stage=stage,
        message=f"{agent.agent_name} produced output and passed guardrails.",
    )

    # Phase D: hand off to a downstream agent so it can build on this output.
    if handoff_to:
        summary = handoff_summary or _summarize_output(result.output)
        send_message(
            db,
            project_id=project_id,
            sender=agent.agent_name,
            recipient=handoff_to,
            content=summary,
            message_type="handoff",
            stage=stage,
        )

    return AgentRunResult(
        output=result.output,
        usage=result.usage,
        run_id=run.id,
        agent_name=agent.agent_name,
    )


def _summarize_output(output: dict[str, object]) -> str:
    """Produce a compact text summary of agent output for an A2A handoff."""
    parts: list[str] = []
    for key, value in output.items():
        if isinstance(value, str):
            text = value
        elif isinstance(value, list):
            text = ", ".join(str(_name_of(item)) for item in value[:5])
        else:
            text = str(value)
        parts.append(f"{key}: {text[:300]}")
    return "\n".join(parts)[:1500]


def _name_of(item: object) -> object:
    """Return a readable label for a list item that may be a dict or scalar."""
    if isinstance(item, dict):
        for key in ("name", "title", "risk", "component", "competitor", "persona"):
            if item.get(key):
                return item[key]
    return item
