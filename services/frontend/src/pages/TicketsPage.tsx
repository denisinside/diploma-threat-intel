import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQueries } from "@tanstack/react-query";
import type { ColumnDef } from "@tanstack/react-table";
import { ChevronDown } from "lucide-react";
import { DataTable } from "@/components/ui/DataTable";
import { SectionCard } from "@/components/ui/SectionCard";
import { SeverityBadge } from "@/components/ui/SeverityBadge";
import { StatCard } from "@/components/ui/StatCard";
import { useCreateTicket, useTicketCount, useTickets, useUpdateTicket } from "@/features/tickets/hooks";
import { useAssets } from "@/features/assets/hooks";
import { vulnsApi } from "@/features/vulns/api";
import { useVulnSearch } from "@/features/vulns/hooks";
import { useAuth } from "@/hooks/useAuth";
import { useCanManageTickets } from "@/hooks/useRoleGuard";
import { formatDate } from "@/lib/format";
import { toast } from "@/lib/toast";
import type { Ticket, TicketStatus } from "@/types";

const statusOptions: Array<TicketStatus | "all"> = [
  "all",
  "open",
  "in_progress",
  "resolved",
  "ignored",
  "false_positive",
];

const statusChangeOptions: TicketStatus[] = [
  "open",
  "in_progress",
  "resolved",
  "ignored",
  "false_positive",
];

function getCveId(v: { aliases?: string[]; id?: string }): string {
  return v.aliases?.find((a) => String(a).toUpperCase().startsWith("CVE-")) ?? v.id ?? "";
}

export function TicketsPage() {
  const { session } = useAuth();
  const companyId = session?.user?.company_id;
  const canManageTickets = useCanManageTickets();
  const [status, setStatus] = useState<TicketStatus | "all">("all");
  const [assetId, setAssetId] = useState("");
  const [vulnerabilityId, setVulnerabilityId] = useState("");
  const [cveSearchQuery, setCveSearchQuery] = useState("");
  const [notes, setNotes] = useState("");
  const [ticketError, setTicketError] = useState("");
  const createTicket = useCreateTicket();
  const updateTicket = useUpdateTicket();

  const { data: assets = [] } = useAssets(companyId);
  const { data: vulnSearch } = useVulnSearch({
    q: cveSearchQuery.length >= 2 ? cveSearchQuery : "CVE-2024",
    limit: 15,
  });
  const vulnSuggestions = cveSearchQuery.length >= 2 ? (vulnSearch?.items ?? []) : [];

  const { data: tickets = [], isLoading, error } = useTickets(
    companyId,
    status === "all" ? undefined : status
  );
  const { data: openCount } = useTicketCount(companyId, "open");
  const { data: inProgressCount } = useTicketCount(companyId, "in_progress");
  const { data: resolvedCount } = useTicketCount(companyId, "resolved");

  const uniqueVulnIds = useMemo(
    () => [...new Set(tickets.map((t) => t.vulnerability_id).filter(Boolean))],
    [tickets]
  );
  const vulnQueries = useQueries({
    queries: uniqueVulnIds.map((id) => ({
      queryKey: ["vulns", id],
      queryFn: () => vulnsApi.getById(id),
      staleTime: 5 * 60 * 1000,
    })),
  });
  const vulnIdToCve = useMemo(() => {
    const map = new Map<string, string>();
    vulnQueries.forEach((q, i) => {
      const id = uniqueVulnIds[i];
      if (!id) return;
      const vuln = q.data;
      if (vuln) {
        const cve = getCveId(vuln);
        map.set(id, cve || id);
      } else {
        map.set(id, id);
      }
    });
    return map;
  }, [vulnQueries, uniqueVulnIds]);

  const columns = useMemo<Array<ColumnDef<Ticket>>>(
    () => [
      { header: "Ticket ID", accessorKey: "_id", cell: ({ row }) => <span className="font-mono text-xs">{String(row.original._id).slice(-8)}</span> },
      {
        header: "Asset",
        id: "asset",
        accessorFn: (row) => {
          const a = assets.find((x) => x._id === row.asset_id);
          return a ? `${a.name}${a.version ? ` ${a.version}` : ""}` : row.asset_id;
        },
        cell: ({ row }) => {
          const aid = row.original.asset_id;
          const asset = assets.find((a) => a._id === aid);
          return asset ? `${asset.name}${asset.version ? ` ${asset.version}` : ""}` : aid;
        },
      },
      {
        header: "Vulnerability",
        id: "vulnerability",
        accessorKey: "vulnerability_id",
        cell: ({ row }) => {
          const vid = row.original.vulnerability_id;
          const display = vulnIdToCve.get(vid) ?? vid;
          return (
            <Link
              to={`/vulnerabilities/${encodeURIComponent(display)}`}
              className="font-mono text-sm text-tactical-sky hover:underline"
            >
              {display}
            </Link>
          );
        },
      },
      {
        header: "Priority",
        accessorKey: "priority",
        cell: ({ row }) => <SeverityBadge severity={row.original.priority} />,
      },
      { header: "Status", accessorKey: "status" },
      {
        header: "Detected",
        accessorKey: "detected_at",
        cell: ({ row }) => formatDate(row.original.detected_at),
      },
      {
        header: "Actions",
        id: "actions",
        enableSorting: false,
        cell: ({ row }) =>
          canManageTickets ? (
            <div className="relative group">
              <select
                value={row.original.status}
                onChange={(e) => {
                  const newStatus = e.target.value as TicketStatus;
                  updateTicket.mutate({
                    ticketId: row.original._id,
                    payload: { status: newStatus },
                  });
                }}
                className="appearance-none bg-slate-800/60 border border-slate-600 rounded px-2 py-1 pr-6 text-xs cursor-pointer hover:border-slate-500"
              >
                {statusChangeOptions.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt.replace("_", " ")}
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-1 top-1/2 -translate-y-1/2 w-3 h-3 pointer-events-none text-slate-400" />
            </div>
          ) : (
            <span className="text-slate-500 text-xs">—</span>
          ),
      },
    ],
    [updateTicket, assets, canManageTickets, vulnIdToCve]
  );

  const handleCreateTicket = (e: React.FormEvent) => {
    e.preventDefault();
    setTicketError("");
    if (!companyId) return;
    if (!assetId.trim() || !vulnerabilityId.trim()) {
      setTicketError("Select an asset and a vulnerability.");
      return;
    }
    createTicket.mutate(
      {
        company_id: companyId,
        asset_id: assetId.trim(),
        vulnerability_id: vulnerabilityId.trim(),
        notes: notes.trim() || undefined,
      },
      {
        onSuccess: () => {
          setAssetId("");
          setVulnerabilityId("");
          setCveSearchQuery("");
          setNotes("");
        },
        onError: (err) => {
          setTicketError(err instanceof Error ? err.message : "Failed to create ticket.");
          toast.error(err instanceof Error ? err.message : "Failed to create ticket.");
        },
      }
    );
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-slate-100">Tickets</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard label="Open" value={openCount?.count ?? 0} accent="amber" />
        <StatCard label="In Progress" value={inProgressCount?.count ?? 0} accent="sky" />
        <StatCard label="Resolved" value={resolvedCount?.count ?? 0} accent="sky" />
      </div>

      <SectionCard
        title={`Vulnerability Tickets (${tickets.length})`}
        rightSlot={
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value as TicketStatus | "all")}
            className="bg-slate-800/60 border border-slate-600 rounded px-2 py-1 text-xs"
          >
            {statusOptions.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        }
      >
        {companyId && canManageTickets ? (
          <form
            className="mb-4 grid grid-cols-1 md:grid-cols-4 gap-2"
            onSubmit={handleCreateTicket}
          >
            <div className="relative">
              <label className="block text-xs text-slate-400 mb-1">Asset</label>
              <select
                value={assetId}
                onChange={(e) => setAssetId(e.target.value)}
                className="w-full bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm"
                required
              >
                <option value="">Select asset...</option>
                {assets.map((a) => (
                  <option key={a._id} value={a._id}>
                    {a.name}
                    {a.version ? ` ${a.version}` : ""} ({a.type})
                  </option>
                ))}
              </select>
            </div>
            <div className="relative">
              <label className="block text-xs text-slate-400 mb-1">Vulnerability (CVE)</label>
              <div className="relative">
                <input
                  value={cveSearchQuery || vulnerabilityId}
                  onChange={(e) => {
                    const v = e.target.value;
                    setCveSearchQuery(v);
                    if (/^CVE-\d{4}-\d+$/i.test(v)) setVulnerabilityId(v);
                    else if (!v) setVulnerabilityId("");
                  }}
                  onBlur={() => {
                    if (/^CVE-\d{4}-\d+$/i.test(cveSearchQuery)) setVulnerabilityId(cveSearchQuery);
                  }}
                  placeholder="Search or type CVE-YYYY-NNNNN"
                  className="w-full bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm"
                />
                {cveSearchQuery.length >= 2 && vulnSuggestions.length > 0 ? (
                  <ul className="absolute z-10 mt-1 w-full max-h-48 overflow-auto bg-slate-800 border border-slate-600 rounded shadow-lg">
                    {vulnSuggestions.map((v) => {
                      const cve = getCveId(v);
                      return (
                        <li key={v.id}>
                          <button
                            type="button"
                            onClick={() => {
                              setVulnerabilityId(cve);
                              setCveSearchQuery(cve);
                            }}
                            className="w-full text-left px-3 py-2 text-sm hover:bg-slate-700"
                          >
                            {cve}
                            {v.database_specific?.severity ? ` (${v.database_specific.severity})` : ""}
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                ) : null}
              </div>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Notes</label>
              <input
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Optional"
                className="w-full bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm"
              />
            </div>
            <div className="flex items-end">
              <button
                type="submit"
                disabled={!assetId || !vulnerabilityId}
                className="rounded border border-tactical-sky/40 text-tactical-sky hover:bg-tactical-sky/15 text-sm px-3 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {createTicket.isPending ? "Creating..." : "Create ticket"}
              </button>
            </div>
          </form>
        ) : null}
        {ticketError ? <p className="mb-2 text-sm text-red-300">{ticketError}</p> : null}
        {error ? <p className="text-sm text-red-300">{(error as Error).message}</p> : null}
        {!canManageTickets && companyId ? (
          <p className="mb-2 text-sm text-slate-400">View-only: you cannot create or update tickets.</p>
        ) : null}
        {isLoading ? (
          <p className="text-slate-400">Loading...</p>
        ) : (
          <DataTable data={tickets} columns={columns} emptyText="No tickets for selected status." />
        )}
      </SectionCard>

      {!companyId ? (
        <p className="text-sm text-amber-300">
          Your account has no `company_id`, so company-scoped tickets are unavailable.
        </p>
      ) : null}
    </div>
  );
}
