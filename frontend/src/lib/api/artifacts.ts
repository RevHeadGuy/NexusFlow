import { api, API_URL } from "./client";
import type { Artifact, ArtifactVersion } from "@/lib/types/api";

export const artifactsApi = {
  list: (projectId: string) =>
    api.get<Artifact[]>(`/projects/${projectId}/artifacts`),
  get: (projectId: string, artifactId: string) =>
    api.get<Artifact>(`/projects/${projectId}/artifacts/${artifactId}`),
  create: (projectId: string, data: { name: string; type: string; content: string }) =>
    api.post<Artifact>(`/projects/${projectId}/artifacts`, data),
  versions: (projectId: string, artifactId: string) =>
    api.get<ArtifactVersion[]>(`/projects/${projectId}/artifacts/${artifactId}/versions`),
  addVersion: (
    projectId: string,
    artifactId: string,
    data: { content: string; summary?: string }
  ) =>
    api.post<ArtifactVersion>(
      `/projects/${projectId}/artifacts/${artifactId}/versions`,
      data
    ),
  exportUrl: (projectId: string, artifactId: string) =>
    `${API_URL}/projects/${projectId}/artifacts/${artifactId}/export`,
};
