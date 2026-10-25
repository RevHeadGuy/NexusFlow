import { api } from "./client";
import type { DashboardStats, GuardrailViolation } from "@/lib/types/api";

export const dashboardApi = {
  stats: () => api.get<DashboardStats>("/dashboard/stats"),
  violations: (projectId: string, unresolvedOnly = false) =>
    api.get<GuardrailViolation[]>(
      `/projects/${projectId}/guardrail-violations${unresolvedOnly ? "?unresolved_only=true" : ""}`
    ),
  overrideViolation: (
    projectId: string,
    violationId: string,
    data: { override_note: string; overridden_by?: string }
  ) =>
    api.post<GuardrailViolation>(
      `/projects/${projectId}/guardrail-violations/${violationId}/override`,
      data
    ),
};
