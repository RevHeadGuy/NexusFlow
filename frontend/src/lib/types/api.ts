// Types that mirror the backend Pydantic schemas

export interface Project {
  id: string;
  name: string;
  description: string | null;
  idea: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  description?: string;
  idea: string;
}

export interface ProjectBrief {
  id: string;
  project_id: string;
  problem_statement: string;
  target_users: string[];
  goals: string[];
  constraints: string[];
  success_criteria: string[];
  clarifying_questions: string[];
  created_at: string;
  updated_at: string;
  token_usage?: {
    provider: string;
    model: string;
    input_tokens: number | null;
    output_tokens: number | null;
    total_tokens: number | null;
  } | null;
}

export interface WorkflowDecision {
  id: string;
  workflow_run_id: string;
  project_id: string;
  stage: string;
  action: string;
  notes: string | null;
  reviewer_name?: string | null;
  reviewer_email?: string | null;
  created_at: string;
}

export interface Workflow {
  id: string;
  project_id: string;
  current_stage: string;
  status: string;
  last_decision: string | null;
  decision: string | null;
  created_at: string;
  updated_at: string;
  template_key: string;
  stage_plan: string[];
  ready_for_approval: boolean;
  review_issues: string[];
  decisions: WorkflowDecision[];
}

export interface WorkflowReviewQueueItem {
  workflow_id: string;
  project_id: string;
  project_name: string;
  current_stage: string;
  status: string;
  updated_at: string;
  ready_for_approval: boolean;
  review_issues: string[];
  unresolved_comment_count: number;
  blocking_guardrail_count: number;
}

export interface ResearchSource {
  id: string;
  project_id: string;
  title: string;
  url: string;
  finding: string;
  notes: string | null;
  added_by: string;
  reviewed: boolean;
  created_at: string;
  updated_at: string;
}

export interface ArtifactReviewComment {
  id: string;
  project_id: string;
  artifact_id: string;
  version_number: number;
  reviewer_name: string;
  section_key: string;
  comment: string;
  suggested_edit: string | null;
  resolved: boolean;
  created_at: string;
  resolved_at: string | null;
}

export interface Artifact {
  id: string;
  project_id: string;
  name: string;
  type: string;
  content: string;
  current_version: number;
  created_at: string;
  updated_at: string;
}

export interface ArtifactVersion {
  id: string;
  artifact_id: string;
  project_id: string;
  version: number;
  content: string;
  summary: string | null;
  created_at: string;
}

export interface EvaluationFinding {
  id: string;
  report_id: string;
  category: string;
  severity: string;
  title: string;
  description: string;
  evidence: string | null;
  recommendation: string | null;
  created_at: string;
}

export interface EvaluationReport {
  id: string;
  project_id: string;
  report_type: string;
  status: string;
  summary: string;
  findings?: EvaluationFinding[];
  created_at: string;
  updated_at: string;
}

export interface ProjectTrace {
  id: string;
  project_id: string;
  event: string;
  stage: string;
  message: string;
  details: Record<string, unknown> | null;
  created_at: string;
}

// Guardrails
export interface GuardrailViolation {
  id: string;
  project_id: string;
  stage: string;
  agent_name: string;
  rule_name: string;
  severity: "low" | "medium" | "high" | "critical";
  message: string;
  detail: Record<string, unknown> | null;
  auto_blocked: boolean;
  overridden_by: string | null;
  override_note: string | null;
  resolved_at: string | null;
  created_at: string;
}

// HITL
export interface Checkpoint {
  id: string;
  project_id: string;
  stage: string;
  status: "pending" | "approved" | "approved_with_edits" | "rejected";
  checkpoint_type: string;
  agent_output: Record<string, unknown> | null;
  human_feedback: Record<string, unknown> | null;
  reviewer_notes: string | null;
  reviewed_by: string | null;
  expires_at: string | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ArtifactFeedback {
  id: string;
  checkpoint_id: string;
  artifact_id: string;
  project_id: string;
  section_key: string;
  comment: string;
  suggested_edit: string | null;
  resolved: boolean;
  created_at: string;
}

// MLOps
export interface AgentRun {
  id: string;
  project_id: string;
  stage: string;
  agent_name: string;
  prompt_version: number;
  model_id: string;
  status: "running" | "success" | "failed" | "guardrail_blocked";
  input_tokens: number | null;
  output_tokens: number | null;
  latency_ms: number | null;
  error_message: string | null;
  evaluation_score: number | null;
  started_at: string;
  completed_at: string | null;
  raw_input?: unknown;
  raw_output?: unknown;
}

export interface PromptVersion {
  id: string;
  agent_name: string;
  version: number;
  content: string;
  change_note: string | null;
  is_active: boolean;
  created_at: string;
  deprecated_at: string | null;
}

export interface EvaluationScore {
  id: string;
  agent_run_id: string;
  metric_name: string;
  score: number;
  explanation: string | null;
  created_at: string;
}

export interface DashboardStats {
  total_projects: number;
  projects_by_status: Record<string, number>;
  workflows_by_stage: Record<string, number>;
  workflows_by_status: Record<string, number>;
  pending_checkpoints: number;
  blocking_violations: number;
  recent_agent_runs: Array<{
    id: string;
    project_id: string;
    agent_name: string;
    stage: string;
    status: string;
    started_at: string;
  }>;
}
