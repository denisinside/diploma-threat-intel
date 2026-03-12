import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip as RechartsTooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Filter, Search } from "lucide-react";
import type { ColumnDef } from "@tanstack/react-table";
import { DataTable } from "@/components/ui/DataTable";
import { SectionCard } from "@/components/ui/SectionCard";
import { SeverityBadge } from "@/components/ui/SeverityBadge";
import { Pagination } from "@/components/ui/Pagination";
import { Tooltip } from "@/components/ui/Tooltip";
import { StatCard } from "@/components/ui/StatCard";
import { useVulnSearch, useVulnStats, useEcosystems } from "@/features/vulns/hooks";
import { VulnAdvancedSearchModal } from "@/features/vulns/VulnAdvancedSearchModal";
import { normalizeSeverity, getCvssScore } from "@/lib/format";
import { useAuth } from "@/hooks/useAuth";
import type { Vulnerability } from "@/types";
import type { VulnSearchParams } from "@/features/vulns/api";

const PAGE_SIZE = 25;
const AGING_COLORS: Record<string, string> = {
  critical: "#ef4444",
  high: "#f97316",
  moderate: "#eab308",
  low: "#22c55e",
};

function getCveId(v: Vulnerability): string {
  return v.aliases?.find((a) => a.toUpperCase().startsWith("CVE-")) ?? v.id;
}

export function VulnerabilitiesPage() {
  const { session } = useAuth();
  const companyId = session?.user?.company_id;
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState<
    Omit<VulnSearchParams, "skip" | "limit" | "sort_by" | "sort_order">
  >({});
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState<string>("published");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [advancedOpen, setAdvancedOpen] = useState(false);

  const searchParams: VulnSearchParams = {
    ...filters,
    skip: (page - 1) * PAGE_SIZE,
    limit: PAGE_SIZE,
    sort_by: sortBy,
    sort_order: sortOrder,
  };

  const { data: searchResult, isLoading, error } = useVulnSearch(searchParams);
  const { data: stats, isLoading: statsLoading } = useVulnStats({ all: true, company_id: companyId });
  const { data: ecosystems = [] } = useEcosystems();

  const vulnerabilities = searchResult?.items ?? [];
  const total = searchResult?.total ?? 0;

  const columns = useMemo<Array<ColumnDef<Vulnerability>>>(
    () => [
      {
        header: "CVE ID",
        cell: ({ row }) => {
          const cve = getCveId(row.original);
          return (
            <Link
              to={`/vulnerabilities/${encodeURIComponent(cve)}`}
              className="text-tactical-sky hover:underline"
            >
              {cve}
            </Link>
          );
        },
      },
      {
        header: "GHSA ID",
        cell: ({ row }) =>
          row.original.id.startsWith("GHSA-") ? (
            <Link
              to={`/vulnerabilities/${encodeURIComponent(getCveId(row.original))}`}
              className="text-tactical-sky hover:underline"
            >
              {row.original.id}
            </Link>
          ) : (
            <span className="text-slate-500">—</span>
          ),
      },
      {
        header: "CVSS",
        cell: ({ row }) => {
          const score = getCvssScore(row.original);
          return score != null ? (
            <span className="font-mono text-sm">{score.toFixed(1)}</span>
          ) : (
            <span className="text-slate-500">—</span>
          );
        },
      },
      {
        header: "Severity",
        cell: ({ row }) => (
          <SeverityBadge severity={normalizeSeverity(row.original.database_specific?.severity)} />
        ),
      },
      {
        header: "Summary",
        cell: ({ row }) => (
          <span className="line-clamp-2 max-w-[320px]">
            {row.original.summary ?? row.original.details ?? "—"}
          </span>
        ),
      },
      {
        header: "Package",
        cell: ({ row }) =>
          row.original.affected?.[0]?.package?.name ?? "—",
      },
      {
        header: "Ecosystem",
        cell: ({ row }) =>
          row.original.affected?.[0]?.package?.ecosystem ?? "—",
      },
      {
        header: "Published",
        cell: ({ row }) =>
          row.original.published
            ? new Date(row.original.published).toLocaleDateString()
            : "—",
      },
    ],
    []
  );

  function onSearch() {
    const q = query.trim();
    if (q.length >= 2) {
      setFilters((prev) => ({ ...prev, q }));
      setPage(1);
    }
  }

  function onApplyFilters(newFilters: typeof filters) {
    setFilters(newFilters);
    setPage(1);
  }

  const kpis = stats?.kpis;
  const topAssetsBars = stats?.charts.top_assets_open_cves ?? [];
  const agingBars = stats?.charts.aging_by_severity ?? [];
  const scatterPoints = stats?.charts.criticality_vs_exploitability ?? [];

  const chartTooltipStyle = {
    backgroundColor: "#1e293b",
    border: "1px solid #475569",
    borderRadius: "4px",
    padding: "8px 12px",
  };

  const mttrHint = useMemo(() => {
    if (!kpis || kpis.mttr_days == null) return "Insufficient resolved data";
    const delta = kpis.mttr_delta_prev_month_days;
    if (delta == null) return "No previous month baseline";
    if (delta < 0) return `▼ ${Math.abs(delta).toFixed(1)}d vs previous month`;
    if (delta > 0) return `▲ ${delta.toFixed(1)}d vs previous month`;
    return "No change vs previous month";
  }, [kpis]);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-slate-100">Vulnerabilities</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard
          label="Total Vulnerabilities"
          value={statsLoading ? "..." : (kpis?.total_vulnerabilities ?? 0).toLocaleString()}
          accent="sky"
          hint="All CVEs in database"
        />
        <StatCard
          label="Open CVEs"
          value={statsLoading ? "..." : (kpis?.open_cves ?? 0).toLocaleString()}
          accent="amber"
          hint="Unresolved tickets for company"
        />
        <StatCard
          label="Critical & Actionable"
          value={statsLoading ? "..." : `${(kpis?.critical_actionable ?? 0).toLocaleString()} 🔥`}
          accent="amber"
          hint="OPEN + CVSS > 9.0"
        />
        <StatCard
          label="MTTR"
          value={statsLoading || kpis?.mttr_days == null ? "..." : `${kpis.mttr_days.toFixed(1)} days`}
          accent="sky"
          hint={statsLoading ? "Calculating..." : mttrHint}
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <SectionCard
          title={
            <Tooltip content="Technologies/assets with highest count of OPEN CVEs (asset.name = package.name)">
              Top Vulnerable Assets
            </Tooltip>
          }
        >
          <div className="h-[260px]">
            {statsLoading ? (
              <div className="h-full animate-pulse rounded bg-slate-800/50" />
            ) : topAssetsBars.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topAssetsBars} layout="vertical" margin={{ left: 0, right: 10, top: 8, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis type="number" stroke="#94a3b8" />
                  <YAxis
                    type="category"
                    dataKey="asset"
                    width={180}
                    interval={0}
                    tick={{ fill: "#94a3b8", fontSize: 11 }}
                    stroke="#94a3b8"
                  />
                  <RechartsTooltip contentStyle={chartTooltipStyle} formatter={(v: number) => [v.toLocaleString(), "Open CVEs"]} />
                  <Bar dataKey="count" fill="#38BDF8" radius={[0, 6, 6, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-slate-400">No company-scoped asset/CVE matches yet.</p>
            )}
          </div>
        </SectionCard>

        <SectionCard
          title={
            <Tooltip content="Aging buckets (days open) stacked by severity for SLA monitoring">
              Vulnerability Aging (SLA)
            </Tooltip>
          }
        >
          <div className="h-[260px]">
            {statsLoading ? (
              <div className="h-full animate-pulse rounded bg-slate-800/50" />
            ) : agingBars.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={agingBars} margin={{ top: 5, right: 20, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="bucket" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <RechartsTooltip contentStyle={chartTooltipStyle} />
                  <Legend />
                  <Bar dataKey="critical" stackId="aging" fill={AGING_COLORS.critical} />
                  <Bar dataKey="high" stackId="aging" fill={AGING_COLORS.high} />
                  <Bar dataKey="moderate" stackId="aging" fill={AGING_COLORS.moderate} />
                  <Bar dataKey="low" stackId="aging" fill={AGING_COLORS.low} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-slate-400">No aging data yet.</p>
            )}
          </div>
        </SectionCard>
      </div>

      <SectionCard
        title={
          <Tooltip content="X: CVSS score, Y: EPSS percentage. Upper-right points are highest priority">
            Criticality vs Exploitability
          </Tooltip>
        }
      >
        <div className="h-[320px]">
          {statsLoading ? (
            <div className="h-full animate-pulse rounded bg-slate-800/50" />
          ) : scatterPoints.length ? (
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  type="number"
                  dataKey="cvss"
                  domain={[0, 10]}
                  tickCount={11}
                  stroke="#94a3b8"
                  name="CVSS"
                />
                <YAxis
                  type="number"
                  dataKey="epss"
                  domain={[0, 1]}
                  stroke="#94a3b8"
                  name="EPSS"
                  tickFormatter={(value) => `${Math.round(value * 100)}%`}
                />
                <RechartsTooltip
                  contentStyle={chartTooltipStyle}
                  formatter={(value: number, key: string) => {
                    if (key === "epss") return [`${(value * 100).toFixed(2)}%`, "EPSS"];
                    return [value.toFixed(2), key.toUpperCase()];
                  }}
                  labelFormatter={(_, payload) => payload?.[0]?.payload?.id ?? "CVE"}
                />
                <Scatter data={scatterPoints} fill="#38BDF8" />
              </ScatterChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-slate-400">No CVSS+EPSS data for open company vulnerabilities.</p>
          )}
        </div>
      </SectionCard>

      <SectionCard
        title="Search"
        rightSlot={
          <button
            type="button"
            onClick={() => setAdvancedOpen(true)}
            className="flex items-center gap-2 px-3 py-1.5 rounded border border-slate-600 text-slate-400 hover:bg-slate-700/50 text-sm"
          >
            <Filter className="w-4 h-4" />
            Advanced
          </button>
        }
      >
        <div className="flex flex-wrap gap-3">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && onSearch()}
            className="min-w-[280px] flex-1 bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm"
            placeholder="Search CVE / summary / details (min 2 chars)"
          />
          <button
            type="button"
            onClick={onSearch}
            className="flex items-center gap-2 px-4 py-2 rounded border border-tactical-sky/40 text-tactical-sky hover:bg-tactical-sky/15"
          >
            <Search className="w-4 h-4" />
            Search
          </button>
        </div>
        <p className="mt-2 text-xs text-slate-500">
          Ecosystems: {ecosystems.slice(0, 10).join(", ") || "No data"}
        </p>
        {error ? (
          <p className="mt-3 text-sm text-red-300">{(error as Error).message}</p>
        ) : null}
      </SectionCard>

      {/* Table */}
      <SectionCard
        title={
          <Tooltip content="Actual total matching your search, not limited by page size">
            Active Vulnerabilities ({total.toLocaleString()})
          </Tooltip>
        }
        rightSlot={
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-500">Sort:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="bg-slate-800/60 border border-slate-600 rounded px-2 py-1 text-slate-300"
            >
              <option value="published">Published</option>
              <option value="modified">Modified</option>
              <option value="cvss">CVSS</option>
              <option value="id">ID</option>
            </select>
            <select
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value as "asc" | "desc")}
              className="bg-slate-800/60 border border-slate-600 rounded px-2 py-1 text-slate-300"
            >
              <option value="desc">Desc</option>
              <option value="asc">Asc</option>
            </select>
          </div>
        }
      >
        {isLoading ? (
          <p className="text-slate-400 py-8">Loading...</p>
        ) : (
          <>
            <DataTable
              data={vulnerabilities}
              columns={columns}
              emptyText="No vulnerabilities found. Try different search terms or filters."
            />
            <Pagination
              page={page}
              pageSize={PAGE_SIZE}
              total={total}
              onPageChange={setPage}
            />
          </>
        )}
      </SectionCard>

      <VulnAdvancedSearchModal
        open={advancedOpen}
        onOpenChange={setAdvancedOpen}
        filters={filters}
        onApply={onApplyFilters}
        ecosystems={ecosystems}
      />
    </div>
  );
}
