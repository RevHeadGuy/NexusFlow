import { api } from "./client";
import type { AgentRun, EvaluationScore, PromptVersion } from "@/lib/types/api";

export const mlopsApi = {
  runs: (params?: {
    project_id?: string;
    agent_name?: string;
    status?: string;
    limit?: number;
    offset?: number;
  }) => {
    const qs = new URLSearchParams();
    if (params?.project_id) qs.set("project_id", params.project_id);
    if (params?.agent_name) qs.set("agent_name", params.agent_name);
    if (params?.status) qs.set("status", params.status);
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.offset) qs.set("offset", String(params.offset));
    const query = qs.toString();
    return api.get<AgentRun[]>(`/mlops/runs${query ? `?${query}` : ""}`);
  },
  getRun: (runId: string) => api.get<AgentRun>(`/mlops/runs/${runId}`),
  getRunScores: (runId: string) =>
    api.get<EvaluationScore[]>(`/mlops/runs/${runId}/scores`),

  prompts: (agentName: string) =>
    api.get<PromptVersion[]>(`/mlops/prompts/${agentName}`),
  createPrompt: (
    agentName: string,
    data: { content: string; change_note?: string; activate?: boolean }
  ) => api.post<PromptVersion>(`/mlops/prompts/${agentName}`, data),
  activatePrompt: (agentName: string, version: number) =>
    api.put<PromptVersion>(`/mlops/prompts/${agentName}/${version}/activate`),

  costSummary: (projectId?: string) =>
    api.get<Record<string, unknown>>(
      `/mlops/cost-summary${projectId ? `?project_id=${projectId}` : ""}`
    ),
  metrics: (agentName?: string) =>
    api.get<Record<string, unknown>>(
      `/mlops/metrics${agentName ? `?agent_name=${agentName}` : ""}`
    ),
};
