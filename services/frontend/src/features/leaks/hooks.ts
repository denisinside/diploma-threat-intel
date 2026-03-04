import { useQuery } from "@tanstack/react-query";
import { leaksApi } from "./api";

type SearchParams = {
  q?: string;
  domain?: string;
  email?: string;
  email_pattern?: string;
};

export function useLeakSources() {
  return useQuery({
    queryKey: ["leak-sources"],
    queryFn: () => leaksApi.getSources(0, 300),
  });
}

export function useLeakSearch(params: SearchParams) {
  const enabled = Boolean(params.q || params.domain || params.email || params.email_pattern);
  return useQuery({
    queryKey: ["leak-search", params],
    queryFn: () => leaksApi.search({ ...params, limit: 300 }),
    enabled,
  });
}
