import { api } from "./client";
import type { ArtifactReviewComment } from "@/lib/types/api";

export const reviewsApi = {
  list: (projectId: string, artifactId: string) =>
    api.get<ArtifactReviewComment[]>(`/projects/${projectId}/artifacts/${artifactId}/comments`),
  add: (
    projectId: string,
    artifactId: string,
    data: { version_number: number; reviewer_name: string; section_key: string; comment: string; suggested_edit?: string },
  ) => api.post<ArtifactReviewComment>(`/projects/${projectId}/artifacts/${artifactId}/comments`, data),
  resolve: (projectId: string, artifactId: string, commentId: string) =>
    api.post<ArtifactReviewComment>(`/projects/${projectId}/artifacts/${artifactId}/comments/${commentId}/resolve`),
};
