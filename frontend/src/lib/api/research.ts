import { api } from "./client";
import type { Artifact, ResearchSource } from "@/lib/types/api";

export const researchApi = {
  list: (projectId: string) => api.get<ResearchSource[]>(`/projects/${projectId}/research-sources`),
  add: (projectId: string, data: { title: string; url: string; finding: string; notes?: string; added_by: string }) =>
    api.post<ResearchSource>(`/projects/${projectId}/research-sources`, data),
  review: (projectId: string, sourceId: string, reviewed: boolean) =>
    api.patch<ResearchSource>(`/projects/${projectId}/research-sources/${sourceId}`, { reviewed }),
  remove: (projectId: string, sourceId: string) =>
    api.delete<void>(`/projects/${projectId}/research-sources/${sourceId}`),
  refreshPlan: (projectId: string) =>
    api.post<Artifact>(`/projects/${projectId}/research-plan/refresh`),
};
