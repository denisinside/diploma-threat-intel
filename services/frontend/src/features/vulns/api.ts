import { apiClient } from "@/lib/api";
import type { Vulnerability } from "@/types";

export type VulnSearchParams = {
  q?: string;
  ecosystem?: string;
  package?: string;
  cvss_min?: number;
  cvss_max?: number;
  published_from?: string;
  published_to?: string;
  cwe_id?: string;
  severity?: string;
  skip?: number;
  limit?: number;
  sort_by?: string;
  sort_order?: string;
};

export type VulnSearchResponse = { items: Vulnerability[]; total: number };

export type VulnStatsParams = Omit<
  VulnSearchParams,
  "skip" | "limit" | "sort_by" | "sort_order"
> & {
  all?: boolean;
  company_id?: string;
  chart_scope?: "company" | "global";
};

export type VulnStats = {
  severity_distribution: Array<{ name: string; value: number }>;
  cvss_distribution: Array<{ range: string; value: number }>;
  by_year: Array<{ year: string; value: number }>;
  total: number;
  mongo_total?: number;
  kpis: {
    total_vulnerabilities: number;
    open_cves: number;
    critical_actionable: number;
    mttr_days: number | null;
    mttr_delta_prev_month_days: number | null;
  };
  charts: {
    top_assets_open_cves: Array<{ asset: string; count: number }>;
    aging_by_severity: Array<{
      bucket: string;
      critical: number;
      high: number;
      moderate: number;
      low: number;
    }>;
    criticality_vs_exploitability: Array<{
      id: string;
      cvss: number;
      epss: number;
      severity: string;
      count?: number;
    }>;
    heatmap: Array<{
      weekday: number;
      hour: number;
      count: number;
    }>;
  };
};

export type PackageSuggestion = { name: string; count: number };

export const vulnsApi = {
  search: (params: VulnSearchParams) => {
    const search = new URLSearchParams();
    if (params.q) search.set("q", params.q);
    if (params.ecosystem) search.set("ecosystem", params.ecosystem);
    if (params.package) search.set("package", params.package);
    if (params.cvss_min != null) search.set("cvss_min", String(params.cvss_min));
    if (params.cvss_max != null) search.set("cvss_max", String(params.cvss_max));
    if (params.published_from) search.set("published_from", params.published_from);
    if (params.published_to) search.set("published_to", params.published_to);
    if (params.cwe_id) search.set("cwe_id", params.cwe_id);
    if (params.severity) search.set("severity", params.severity);
    if (params.skip != null) search.set("skip", String(params.skip));
    if (params.limit != null) search.set("limit", String(params.limit));
    if (params.sort_by) search.set("sort_by", params.sort_by);
    if (params.sort_order) search.set("sort_order", params.sort_order);
    return apiClient.get<VulnSearchResponse>(`/vulns/search?${search}`);
  },
  getStats: (params: VulnStatsParams) => {
    const search = new URLSearchParams();
    if (params.all) search.set("all", "true");
    if (params.company_id) search.set("company_id", params.company_id);
    if (params.chart_scope) search.set("chart_scope", params.chart_scope);
    if (params.q) search.set("q", params.q);
    if (params.ecosystem) search.set("ecosystem", params.ecosystem);
    if (params.package) search.set("package", params.package);
    if (params.cvss_min != null) search.set("cvss_min", String(params.cvss_min));
    if (params.cvss_max != null) search.set("cvss_max", String(params.cvss_max));
    if (params.published_from) search.set("published_from", params.published_from);
    if (params.published_to) search.set("published_to", params.published_to);
    if (params.cwe_id) search.set("cwe_id", params.cwe_id);
    if (params.severity) search.set("severity", params.severity);
    return apiClient.get<VulnStats>(`/vulns/stats?${search}`);
  },
  getById: (id: string) => apiClient.get<Vulnerability>(`/vulns/${encodeURIComponent(id)}`),
  searchPackages: (q: string, limit?: number) => {
    const search = new URLSearchParams({ q });
    if (limit != null) search.set("limit", String(limit));
    return apiClient.get<PackageSuggestion[]>(`/vulns/packages/search?${search}`);
  },
  getEcosystems: (skip?: number, limit?: number) => {
    const search = new URLSearchParams();
    if (skip != null) search.set("skip", String(skip));
    if (limit != null) search.set("limit", String(limit));
    return apiClient.get<string[]>(`/vulns/ecosystems?${search}`);
  },
};
