import { useMemo, useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { DataTable } from "@/components/ui/DataTable";
import { Pagination } from "@/components/ui/Pagination";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatCard } from "@/components/ui/StatCard";
import { useLeakAnalytics, useLeakSearch } from "@/features/leaks/hooks";
import { useAuth } from "@/hooks/useAuth";
import type { LeakHeatmapItem, LeakRecord } from "@/types";

const pieColors = ["#38BDF8", "#F59E0B", "#F97316", "#A78BFA", "#22C55E"];
const weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

type QueryType = "domain" | "email" | "email_pattern" | "q";
type SearchParams = { q?: string; domain?: string; email?: string; email_pattern?: string };
const PAGE_SIZE = 25;

function formatNumber(value: number) {
  return new Intl.NumberFormat("en-US").format(value);
}

function formatCompactNumber(value: number) {
  return new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}

function getTrendHint(last24h: number, last7d: number) {
  const avgDaily = last7d > 0 ? last7d / 7 : 0;
  if (last24h > avgDaily) return { text: "↑ above 7d avg", className: "text-red-300" };
  return { text: "↓ below 7d avg", className: "text-emerald-300" };
}

function getHeatColor(value: number, max: number) {
  if (max <= 0) return "rgba(71, 85, 105, 0.25)";
  const intensity = value / max;
  if (intensity > 0.8) return "rgba(239, 68, 68, 0.95)";
  if (intensity > 0.6) return "rgba(245, 158, 11, 0.9)";
  if (intensity > 0.4) return "rgba(56, 189, 248, 0.85)";
  if (intensity > 0.2) return "rgba(59, 130, 246, 0.65)";
  return "rgba(71, 85, 105, 0.4)";
}

const chartTooltipProps = {
  contentStyle: {
    backgroundColor: "#0f172a",
    border: "1px solid #334155",
    borderRadius: "8px",
  },
  labelStyle: { color: "#e2e8f0" },
  itemStyle: { color: "#e2e8f0" },
};

function HeatmapGrid({ items }: { items: LeakHeatmapItem[] }) {
  const valueMap = useMemo(() => {
    const map = new Map<string, number>();
    items.forEach((item) => map.set(`${item.weekday}-${item.hour}`, item.count));
    return map;
  }, [items]);
  const maxValue = useMemo(
    () => items.reduce((max, item) => (item.count > max ? item.count : max), 0),
    [items]
  );

  return (
    <div className="overflow-x-auto">
      <div className="grid gap-1 min-w-[920px]" style={{ gridTemplateColumns: "70px repeat(24, minmax(30px, 1fr))" }}>
        <div />
        {Array.from({ length: 24 }).map((_, hour) => (
          <div key={`h-${hour}`} className="text-[10px] text-slate-400 text-center">
            {String(hour).padStart(2, "0")}
          </div>
        ))}
        {weekdays.map((day, dayIndex) => (
          <div key={day} className="contents">
            <div className="text-xs text-slate-300 pr-2 self-center">{day}</div>
            {Array.from({ length: 24 }).map((_, hour) => {
              const value = valueMap.get(`${dayIndex}-${hour}`) ?? 0;
              return (
                <div
                  key={`${dayIndex}-${hour}`}
                  className="h-5 rounded-sm border border-slate-800/60"
                  style={{ backgroundColor: getHeatColor(value, maxValue) }}
                  title={`${day} ${String(hour).padStart(2, "0")}:00 - ${value}`}
                />
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}

export function LeaksPage() {
  const { session } = useAuth();
  const companyId = session?.user?.company_id;
  const [queryType, setQueryType] = useState<QueryType>("domain");
  const [searchValue, setSearchValue] = useState("");
  const [params, setParams] = useState<SearchParams>({});
  const [page, setPage] = useState(1);

  const searchRequest = useMemo(
    () => ({ ...params, skip: (page - 1) * PAGE_SIZE, limit: PAGE_SIZE }),
    [params, page]
  );
  const { data: searchData, isLoading, error } = useLeakSearch(searchRequest);
  const { data: analytics, isLoading: analyticsLoading } = useLeakAnalytics(params, companyId);
  const leaks = searchData?.items ?? [];
  const totalLeaks = searchData?.total ?? 0;

  const columns = useMemo<Array<ColumnDef<LeakRecord>>>(
    () => [
      { header: "URL", accessorKey: "url" },
      { header: "Domain", accessorKey: "domain" },
      { header: "Email", accessorKey: "email" },
      {
        header: "Password",
        cell: ({ row }) => (
          <span className="font-mono tracking-wider text-slate-200/90">
            {row.original.password || "—"}
          </span>
        ),
      },
      { header: "Type", accessorKey: "leaktype" },
      { header: "Country Code", accessorKey: "country_code" },
      { header: "Ref File", accessorKey: "ref_file" },
      {
        header: "Date",
        cell: ({ row }) => {
          const value = row.original.date;
          if (!value) return "—";
          const date = new Date(value);
          if (Number.isNaN(date.getTime())) return "—";
          return date.toLocaleString();
        },
      },
      {
        header: "Tags",
        cell: ({ row }) => (row.original.tags?.length ? row.original.tags.join(", ") : "—"),
      },
    ],
    []
  );

  const sourceDistribution = analytics?.charts.source_distribution ?? [];
  const trend = analytics?.charts.trend ?? [];
  const passwordHistogram = analytics?.charts.password_histogram ?? [];
  const topDomains = analytics?.charts.top_domains ?? [];
  const heatmap = analytics?.charts.heatmap ?? [];
  const kpis = analytics?.kpis;

  const leakTrendHint = getTrendHint(kpis?.new_leaks_24h ?? 0, kpis?.new_leaks_7d ?? 0);

  function onSearch() {
    if (!searchValue.trim()) return;
    setPage(1);
    setParams({ [queryType]: searchValue.trim() });
  }

  function onReset() {
    setSearchValue("");
    setPage(1);
    setParams({});
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-slate-100">Leaks</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard
          label="Total Compromised Records"
          value={formatNumber(kpis?.total_compromised_records ?? 0)}
          accent="sky"
          hint={<span className={leakTrendHint.className}>{leakTrendHint.text}</span>}
        />
        <div className="glass-panel p-4 border border-tactical-amber/35 flex">
          <div className="flex-1 min-w-0">
            <p className="text-xs uppercase tracking-wide text-slate-400">New Leaks (24h)</p>
            <p className="mt-1 text-2xl leading-none font-semibold text-slate-100">
              {formatNumber(kpis?.new_leaks_24h ?? 0)}
            </p>
            <p className="mt-2 text-xs text-slate-500">
              <span className={leakTrendHint.className}>{leakTrendHint.text}</span>
            </p>
          </div>
          <div className="w-px shrink-0 bg-slate-600/60 mx-3" aria-hidden />
          <div className="flex-1 min-w-0">
            <p className="text-xs uppercase tracking-wide text-slate-400">New Leaks (7d)</p>
            <p className="mt-1 text-2xl leading-none font-semibold text-slate-100">
              {formatNumber(kpis?.new_leaks_7d ?? 0)}
            </p>
            <p className="mt-2 text-xs text-slate-500">Total over last 7 days</p>
          </div>
        </div>
        <StatCard
          label="Monitored Sources"
          value={formatNumber(kpis?.monitored_sources ?? 0)}
          accent="sky"
          hint="Channels/chats in monitoring"
        />
        <StatCard
          label="Critical Alerts"
          value={formatNumber(kpis?.critical_alerts ?? 0)}
          accent="amber"
          hint={
            <span className={kpis?.critical_alerts ? "text-red-300" : "text-emerald-300"}>
              {kpis?.critical_alerts ? "↑ requires action" : "↓ no critical matches"}
            </span>
          }
        />
      </div>

      <SectionCard title="Leak Filters">
        <div className="flex flex-wrap gap-3">
          <select
            value={queryType}
            onChange={(e) => setQueryType(e.target.value as QueryType)}
            className="bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm"
          >
            <option value="domain">Domain</option>
            <option value="email">Email</option>
            <option value="email_pattern">Email Pattern</option>
            <option value="q">Fulltext</option>
          </select>
          <input
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            placeholder="Type query..."
            className="min-w-[280px] flex-1 bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm"
          />
          <button
            type="button"
            onClick={onSearch}
            className="px-4 py-2 rounded border border-tactical-sky/40 text-tactical-sky hover:bg-tactical-sky/15"
          >
            Search
          </button>
          <button
            type="button"
            onClick={onReset}
            className="px-4 py-2 rounded border border-slate-600 text-slate-200 hover:bg-slate-700/40"
          >
            Reset
          </button>
        </div>
        {error ? <p className="mt-3 text-sm text-red-300">{(error as Error).message}</p> : null}
        <p className="mt-3 text-xs text-slate-500">
          {analytics?.meta.filtered
            ? "Charts show filtered data; KPIs remain global."
            : "Global mode: charts and KPIs across all leaks."}
        </p>
      </SectionCard>

      <SectionCard title={`Compromised Data (${formatNumber(totalLeaks)})`}>
        {isLoading ? (
          <p className="text-slate-400">Loading...</p>
        ) : (
          <>
            <DataTable data={leaks} columns={columns} emptyText="Run a search to get leak records." />
            <Pagination
              page={page}
              pageSize={PAGE_SIZE}
              total={totalLeaks}
              onPageChange={(nextPage) => setPage(nextPage)}
            />
          </>
        )}
      </SectionCard>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <SectionCard title="Leak Source Types">
          <div className="h-[260px]">
            {analyticsLoading ? (
              <p className="text-slate-400">Loading...</p>
            ) : sourceDistribution.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={sourceDistribution}
                    dataKey="count"
                    nameKey="label"
                    innerRadius={46}
                    outerRadius={78}
                    label={({ percent }) => `${((percent ?? 0) * 100).toFixed(0)}%`}
                  >
                    {sourceDistribution.map((entry, index) => (
                      <Cell key={entry.source_id} fill={pieColors[index % pieColors.length]} />
                    ))}
                  </Pie>
                  <Tooltip {...chartTooltipProps} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-slate-400">No source distribution data.</p>
            )}
          </div>
        </SectionCard>
        <SectionCard title="Top Exposed Domains">
          <div className="h-[260px]">
            {topDomains.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topDomains} layout="vertical" margin={{ left: 0, right: 10, top: 8, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis type="number" stroke="#94a3b8" tickFormatter={formatCompactNumber} />
                  <YAxis
                    type="category"
                    dataKey="domain"
                    width={140}
                    interval={0}
                    tick={{ fill: "#94a3b8", fontSize: 11 }}
                    stroke="#94a3b8"
                  />
                  <Tooltip {...chartTooltipProps} />
                  <Bar dataKey="count" fill="#38BDF8" radius={[0, 6, 6, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-slate-400">No domain data yet.</p>
            )}
          </div>
        </SectionCard>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <SectionCard title="Leak Dynamics (Last 30 Days)">
          <div className="h-[260px]">
            {trend.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="date" tickFormatter={(value) => String(value).slice(5)} stroke="#94a3b8" />
                  <YAxis
                    width={70}
                    stroke="#94a3b8"
                    tickFormatter={formatCompactNumber}
                    tick={{ fill: "#94a3b8", fontSize: 11 }}
                  />
                  <Tooltip {...chartTooltipProps} />
                  <Legend />
                  <Area type="monotone" dataKey="total" name="Total Leaks" stroke="#38BDF8" fill="#38BDF8" fillOpacity={0.2} />
                  <Area type="monotone" dataKey="company" name="Our Company" stroke="#F97316" fill="#F97316" fillOpacity={0.2} />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-slate-400">No trend data for selected range.</p>
            )}
          </div>
        </SectionCard>

        <SectionCard title="Password Exposure Score">
          <div className="h-[260px]">
            {passwordHistogram.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={passwordHistogram}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="bucket" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" tickFormatter={formatCompactNumber} />
                  <Tooltip {...chartTooltipProps} />
                  <Bar dataKey="count" fill="#F59E0B" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-slate-400">No password histogram data.</p>
            )}
          </div>
        </SectionCard>
      </div>

      <SectionCard title="Threat Actor Activity Heatmap">
        {heatmap.length ? (
          <HeatmapGrid items={heatmap} />
        ) : (
          <p className="text-slate-400">No heatmap data available.</p>
        )}
      </SectionCard>
    </div>
  );
}
