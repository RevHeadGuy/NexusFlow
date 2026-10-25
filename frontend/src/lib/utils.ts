import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatRelative(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export const WORKFLOW_STAGES = [
  { key: "idea_discovery", label: "Idea Discovery", short: "Discovery", output: "Idea brief", description: "Clarify the problem, intended users, goals, and open questions." },
  { key: "market_research", label: "Market Research", short: "Research", output: "Research plan", description: "Plan the questions and sources needed to validate market assumptions. External research is not run yet." },
  { key: "technical_feasibility", label: "Technical Feasibility", short: "Feasibility", output: "Feasibility draft", description: "Identify system areas, constraints, and technical decisions to validate." },
  { key: "prd_architecture", label: "PRD & Architecture", short: "PRD", output: "Requirements and architecture drafts", description: "Turn the approved brief into an initial product and system outline." },
  { key: "quality_review", label: "Quality Review", short: "Review", output: "Consistency and risk review", description: "Run deterministic checks and review findings with their evidence." },
  { key: "final_approval", label: "Final Approval", short: "Approval", output: "Final package guide", description: "Review the saved package contents before marking the workflow complete." },
] as const;

export const SEVERITY_STYLES: Record<string, { badge: string; dot: string }> = {
  low:      { badge: "bg-blue-500/10 text-blue-400 border border-blue-500/20",     dot: "bg-blue-400" },
  medium:   { badge: "bg-amber-500/10 text-amber-400 border border-amber-500/20",  dot: "bg-amber-400" },
  high:     { badge: "bg-orange-500/10 text-orange-400 border border-orange-500/20", dot: "bg-orange-400" },
  critical: { badge: "bg-red-500/10 text-red-400 border border-red-500/20",        dot: "bg-red-500" },
};

export const STATUS_STYLES: Record<string, string> = {
  draft:               "bg-zinc-500/10 text-zinc-400 border border-zinc-500/20",
  active:              "bg-blue-500/10 text-blue-400 border border-blue-500/20",
  completed:           "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20",
  rejected:            "bg-red-500/10 text-red-400 border border-red-500/20",
  in_progress:         "bg-blue-500/10 text-blue-400 border border-blue-500/20",
  awaiting_review:     "bg-amber-500/10 text-amber-400 border border-amber-500/20",
  revision_requested:  "bg-orange-500/10 text-orange-400 border border-orange-500/20",
  pending:             "bg-amber-500/10 text-amber-400 border border-amber-500/20",
  approved:            "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20",
  approved_with_edits: "bg-teal-500/10 text-teal-400 border border-teal-500/20",
  success:             "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20",
  failed:              "bg-red-500/10 text-red-400 border border-red-500/20",
  running:             "bg-blue-500/10 text-blue-400 border border-blue-500/20",
  guardrail_blocked:   "bg-red-500/10 text-red-400 border border-red-500/20",
};

// Keep old names as aliases for compatibility
export const SEVERITY_COLORS = SEVERITY_STYLES;
export const STATUS_COLORS = STATUS_STYLES;
