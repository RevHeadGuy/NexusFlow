import { api } from "./client";
import type { Workflow, WorkflowReviewQueueItem } from "@/lib/types/api";

export const workflowApi = {
  start: (projectId: string, data: { template_key: string; stage_plan: string[] }) =>
    api.post<Workflow>(`/projects/${projectId}/workflow`, data),
  get: (projectId: string) =>
    api.get<Workflow>(`/projects/${projectId}/workflow`),
  decide: (
    projectId: string,
    payload: { stage: string; action: string; notes?: string }
  ) => api.post<Workflow>(`/projects/${projectId}/workflow/decision`, payload),
  prepare: (projectId: string) =>
    api.post<{ stage: string; artifacts: string[]; notice: string }>(`/projects/${projectId}/workflow/prepare`),
  reviewQueue: () => api.get<WorkflowReviewQueueItem[]>("/review-queue/workflows"),
};
