import { useMemo, useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis } from "recharts";
import { DataTable } from "@/components/ui/DataTable";
import { SectionCard } from "@/components/ui/SectionCard";
import { SeverityBadge } from "@/components/ui/SeverityBadge";
import { useEcosystems, useVulnSearch } from "@/features/vulns/hooks";
import { normalizeSeverity } from "@/lib/format";
import type { Vulnerability } from "@/types";

export function VulnerabilitiesPage() {
  const [query, setQuery] = useState("CVE");
  const [submitted, setSubmitted] = useState("CVE");
  const { data: vulnerabilities = [], isLoading, error } = useVulnSearch(submitted);
  const { data: ecosystems = [] } = useEcosystems();

  const columns = useMemo<Array<ColumnDef<Vulnerability>>>(
    () => [
      { header: "ID", accessorKey: "id" },
      {
        header: "Summary",
        cell: ({ row }) => (
          <span className="line-clamp-2 max-w-[420px]">{row.original.summary ?? row.original.details ?? "—"}</span>
        ),
      },
      {
        header: "Severity",
        cell: ({ row }) => (
          <SeverityBadge severity={normalizeSeverity(row.original.database_specific?.severity)} />
        ),
      },
      {
        header: "Affected Package",
        cell: ({ row }) => row.original.affected?.[0]?.package?.name ?? "—",
      },
      {
        header: "Ecosystem",
        cell: ({ row }) => row.original.affected?.[0]?.package?.ecosystem ?? "—",
      },
    ],
    []
  );

  const severityBars = useMemo(() => {
    const stats = { critical: 0, high: 0, medium: 0, low: 0, unknown: 0 };
    vulnerabilities.forEach((v) => {
      stats[normalizeSeverity(v.database_specific?.severity)] += 1;
    });
    return Object.entries(stats).map(([name, value]) => ({ name, value }));
  }, [vulnerabilities]);

  function onSearch() {
    if (query.trim().length < 2) return;
    setSubmitted(query.trim());
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-slate-100">Vulnerabilities</h1>

      <SectionCard title="Search">
        <div className="flex flex-wrap gap-3">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="min-w-[280px] flex-1 bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm"
            placeholder="Search CVE / summary / details"
          />
          <button
            type="button"
            onClick={onSearch}
            className="px-4 py-2 rounded border border-tactical-sky/40 text-tactical-sky hover:bg-tactical-sky/15"
          >
            Search
          </button>
        </div>
        <p className="mt-2 text-xs text-slate-500">
          Ecosystems in DB: {ecosystems.slice(0, 8).join(", ") || "No data"}
        </p>
        {error ? <p className="mt-3 text-sm text-red-300">{(error as Error).message}</p> : null}
      </SectionCard>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2">
          <SectionCard title={`Active Vulnerabilities (${vulnerabilities.length})`}>
            {isLoading ? (
              <p className="text-slate-400">Loading...</p>
            ) : (
              <DataTable data={vulnerabilities} columns={columns} emptyText="No vulnerabilities found." />
            )}
          </SectionCard>
        </div>
        <SectionCard title="Severity Distribution">
          <div className="h-[320px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={severityBars}>
                <XAxis dataKey="name" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Bar dataKey="value" fill="#F59E0B" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
