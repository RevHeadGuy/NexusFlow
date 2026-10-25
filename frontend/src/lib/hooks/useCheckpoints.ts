import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { checkpointsApi } from "@/lib/api/checkpoints";

export const checkpointKeys = {
  list: (projectId: string) => ["checkpoints", projectId] as const,
  queue: ["review-queue"] as const,
  feedback: (artifactId: string) => ["artifact-feedback", artifactId] as const,
};

export function useCheckpoints(projectId: string, pendingOnly = false) {
  return useQuery({
    queryKey: [...checkpointKeys.list(projectId), pendingOnly],
    queryFn: () => checkpointsApi.list(projectId, pendingOnly),
    enabled: !!projectId,
  });
}

export function useReviewQueue() {
  return useQuery({
    queryKey: checkpointKeys.queue,
    queryFn: checkpointsApi.globalQueue,
  });
}

export function useReviewCheckpoint(projectId: string, checkpointId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      action: "approve" | "approve_with_edits" | "reject";
      reviewer_notes?: string;
      human_feedback?: Record<string, unknown>;
    }) => checkpointsApi.review(projectId, checkpointId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: checkpointKeys.list(projectId) });
      qc.invalidateQueries({ queryKey: checkpointKeys.queue });
    },
  });
}

export function useArtifactFeedback(projectId: string, artifactId: string) {
  return useQuery({
    queryKey: checkpointKeys.feedback(artifactId),
    queryFn: () => checkpointsApi.listFeedback(projectId, artifactId),
    enabled: !!projectId && !!artifactId,
  });
}
