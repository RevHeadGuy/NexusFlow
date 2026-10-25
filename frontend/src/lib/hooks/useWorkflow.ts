import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { workflowApi } from "@/lib/api/workflow";

export const workflowKeys = {
  detail: (projectId: string) => ["workflow", projectId] as const,
};

export function useWorkflow(projectId: string) {
  return useQuery({
    queryKey: workflowKeys.detail(projectId),
    queryFn: () => workflowApi.get(projectId),
    enabled: !!projectId,
    retry: false,
  });
}

export function useWorkflowReviewQueue() {
  return useQuery({
    queryKey: ["workflow-review-queue"],
    queryFn: workflowApi.reviewQueue,
    refetchInterval: 30_000,
  });
}

export function useStartWorkflow(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { template_key: string; stage_plan: string[] }) => workflowApi.start(projectId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: workflowKeys.detail(projectId) });
      qc.invalidateQueries({ queryKey: ["projects", projectId] });
      qc.invalidateQueries({ queryKey: ["workflow-review-queue"] });
    },
  });
}

export function useWorkflowDecision(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { stage: string; action: string; notes?: string }) =>
      workflowApi.decide(projectId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: workflowKeys.detail(projectId) });
      qc.invalidateQueries({ queryKey: ["projects", projectId] });
      qc.invalidateQueries({ queryKey: ["workflow-review-queue"] });
    },
  });
}

export function usePrepareWorkflowStage(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => workflowApi.prepare(projectId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["artifacts", projectId] });
      qc.invalidateQueries({ queryKey: workflowKeys.detail(projectId) });
      qc.invalidateQueries({ queryKey: ["workflow-review-queue"] });
    },
  });
}
