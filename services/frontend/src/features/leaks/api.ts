import { apiClient } from "@/lib/api";
import type { LeakRecord, LeakSource } from "@/types";

export const leaksApi = {
  search: (params: {
    q?: string;
    domain?: string;
    email?: string;
    email_pattern?: string;
    skip?: number;
    limit?: number;
  }) => {
    const search = new URLSearchParams();
    if (params.q) search.set("q", params.q);
    if (params.domain) search.set("domain", params.domain);
    if (params.email) search.set("email", params.email);
    if (params.email_pattern) search.set("email_pattern", params.email_pattern);
    if (params.skip != null) search.set("skip", String(params.skip));
    if (params.limit != null) search.set("limit", String(params.limit));
    return apiClient.get<LeakRecord[]>(`/leaks/search?${search}`);
  },
  getSources: (skip?: number, limit?: number) => {
    const search = new URLSearchParams();
    if (skip != null) search.set("skip", String(skip));
    if (limit != null) search.set("limit", String(limit));
    return apiClient.get<LeakSource[]>(`/leaks/sources?${search}`);
  },
};
