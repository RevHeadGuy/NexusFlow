import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { mlopsApi } from "@/lib/api/mlops";

export const mlopsKeys = {
  runs: (params?: Record<string, string>) => ["mlops-runs", params] as const,
  run: (id: string) => ["mlops-run", id] as const,
  runScores: (id: string) => ["mlops-run-scores", id] as const,
  prompts: (agentName: string) => ["mlops-prompts", agentName] as const,
  cost: (projectId?: string) => ["mlops-cost", projectId] as const,
  metrics: (agentName?: string) => ["mlops-metrics", agentName] as const,
};

export function useAgentRuns(params?: {
  project_id?: string;
  agent_name?: string;
  status?: string;
  limit?: number;
}) {
  return useQuery({
    queryKey: mlopsKeys.runs(params as Record<string, string>),
    queryFn: () => mlopsApi.runs(params),
  });
}

export function useAgentRun(runId: string) {
  return useQuery({
    queryKey: mlopsKeys.run(runId),
    queryFn: () => mlopsApi.getRun(runId),
    enabled: !!runId,
  });
}

export function useRunScores(runId: string) {
  return useQuery({
    queryKey: mlopsKeys.runScores(runId),
    queryFn: () => mlopsApi.getRunScores(runId),
    enabled: !!runId,
  });
}

export function usePromptVersions(agentName: string) {
  return useQuery({
    queryKey: mlopsKeys.prompts(agentName),
    queryFn: () => mlopsApi.prompts(agentName),
    enabled: !!agentName,
  });
}

export function useCreatePrompt(agentName: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { content: string; change_note?: string; activate?: boolean }) =>
      mlopsApi.createPrompt(agentName, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: mlopsKeys.prompts(agentName) }),
  });
}

export function useActivatePrompt(agentName: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (version: number) => mlopsApi.activatePrompt(agentName, version),
    onSuccess: () => qc.invalidateQueries({ queryKey: mlopsKeys.prompts(agentName) }),
  });
}

export function useCostSummary(projectId?: string) {
  return useQuery({
    queryKey: mlopsKeys.cost(projectId),
    queryFn: () => mlopsApi.costSummary(projectId),
  });
}

export function useMetrics(agentName?: string) {
  return useQuery({
    queryKey: mlopsKeys.metrics(agentName),
    queryFn: () => mlopsApi.metrics(agentName),
  });
}
