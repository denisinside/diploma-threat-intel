import { apiClient } from "@/lib/api";
import type { Vulnerability } from "@/types";

export const vulnsApi = {
  search: (q: string, skip?: number, limit?: number) => {
    const search = new URLSearchParams({ q });
    if (skip != null) search.set("skip", String(skip));
    if (limit != null) search.set("limit", String(limit));
    return apiClient.get<Vulnerability[]>(`/vulns/search?${search}`);
  },
  getById: (id: string) => apiClient.get<Vulnerability>(`/vulns/${encodeURIComponent(id)}`),
  getEcosystems: (skip?: number, limit?: number) => {
    const search = new URLSearchParams();
    if (skip != null) search.set("skip", String(skip));
    if (limit != null) search.set("limit", String(limit));
    return apiClient.get<string[]>(`/vulns/ecosystems?${search}`);
  },
};
