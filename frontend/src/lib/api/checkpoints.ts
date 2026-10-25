import { api } from "./client";
import type { ArtifactFeedback, Checkpoint } from "@/lib/types/api";

export const checkpointsApi = {
  list: (projectId: string, pendingOnly = false) =>
    api.get<Checkpoint[]>(
      `/projects/${projectId}/checkpoints${pendingOnly ? "?pending_only=true" : ""}`
    ),
  get: (projectId: string, checkpointId: string) =>
    api.get<Checkpoint>(`/projects/${projectId}/checkpoints/${checkpointId}`),
  create: (
    projectId: string,
    data: { stage: string; checkpoint_type?: string; agent_output?: unknown }
  ) => api.post<Checkpoint>(`/projects/${projectId}/checkpoints`, data),
  review: (
    projectId: string,
    checkpointId: string,
    data: {
      action: "approve" | "approve_with_edits" | "reject";
      reviewer_notes?: string;
      human_feedback?: Record<string, unknown>;
      reviewed_by?: string;
    }
  ) =>
    api.post<Checkpoint>(
      `/projects/${projectId}/checkpoints/${checkpointId}/review`,
      data
    ),
  globalQueue: () => api.get<Checkpoint[]>("/review-queue"),

  // Artifact feedback
  addFeedback: (
    projectId: string,
    data: {
      checkpoint_id: string;
      artifact_id: string;
      section_key: string;
      comment: string;
      suggested_edit?: string;
    }
  ) => api.post<ArtifactFeedback>(`/projects/${projectId}/artifact-feedback`, data),
  listFeedback: (projectId: string, artifactId: string, unresolvedOnly = false) =>
    api.get<ArtifactFeedback[]>(
      `/projects/${projectId}/artifacts/${artifactId}/feedback${unresolvedOnly ? "?unresolved_only=true" : ""}`
    ),
  resolveFeedback: (projectId: string, feedbackId: string) =>
    api.post<ArtifactFeedback>(
      `/projects/${projectId}/artifact-feedback/${feedbackId}/resolve`
    ),
};
