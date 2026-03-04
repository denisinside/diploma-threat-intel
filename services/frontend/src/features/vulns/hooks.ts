import { useQuery } from "@tanstack/react-query";
import { vulnsApi } from "./api";

export function useVulnSearch(query: string) {
  return useQuery({
    queryKey: ["vulns", query],
    queryFn: () => vulnsApi.search(query, 0, 300),
    enabled: query.trim().length >= 2,
  });
}

export function useEcosystems() {
  return useQuery({
    queryKey: ["ecosystems"],
    queryFn: () => vulnsApi.getEcosystems(0, 200),
  });
}
