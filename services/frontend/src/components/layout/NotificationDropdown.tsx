import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Bell } from "lucide-react";
import { useTicketCount, useTickets } from "@/features/tickets/hooks";
import { SeverityBadge } from "@/components/ui/SeverityBadge";
import { formatDate } from "@/lib/format";

const MAX_ITEMS = 8;

interface NotificationDropdownProps {
  companyId?: string;
}

export function NotificationDropdown({ companyId }: NotificationDropdownProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const { data: count } = useTicketCount(companyId ?? "", "open");
  const { data: tickets = [] } = useTickets(companyId ?? "", "open");
  const displayTickets = tickets.slice(0, MAX_ITEMS);

  useEffect(() => {
    if (!open) return;
    const onOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onOutside);
    return () => document.removeEventListener("mousedown", onOutside);
  }, [open]);

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="relative p-2 text-slate-400 hover:text-slate-200 rounded-md hover:bg-slate-800/50"
        aria-label="Notifications"
      >
        <Bell className="w-5 h-5" />
        {(count?.count ?? 0) > 0 && (
          <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] flex items-center justify-center text-[10px] font-semibold text-white bg-rose-500 rounded-full px-1">
            {count!.count > 99 ? "99+" : count!.count}
          </span>
        )}
      </button>
      {open && (
        <div className="absolute right-0 top-full mt-1 w-80 max-h-[400px] overflow-y-auto bg-slate-900 border border-slate-700/50 rounded-lg shadow-xl z-[9999]">
          <div className="p-3 border-b border-slate-700/50 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-200">New vulnerability tickets</h3>
            {(count?.count ?? 0) > 0 && (
              <span className="text-xs text-slate-400">{count!.count} open</span>
            )}
          </div>
          <div className="divide-y divide-slate-700/30">
            {!companyId ? (
              <div className="p-4 text-sm text-slate-500">Company-scoped tickets unavailable</div>
            ) : displayTickets.length === 0 ? (
              <div className="p-4 text-sm text-slate-500">No open tickets</div>
            ) : (
              displayTickets.map((t) => (
                <Link
                  key={t._id}
                  to={`/vulnerabilities/${t.vulnerability_id}`}
                  onClick={() => setOpen(false)}
                  className="block p-3 hover:bg-slate-800/50 transition-colors"
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="font-mono text-sm text-slate-200 truncate">
                      {t.vulnerability_id}
                    </span>
                    <SeverityBadge severity={t.priority} />
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">{formatDate(t.detected_at)}</p>
                </Link>
              ))
            )}
          </div>
          {companyId && (count?.count ?? 0) > 0 && (
            <div className="p-2 border-t border-slate-700/50">
              <Link
                to="/tickets"
                onClick={() => setOpen(false)}
                className="block text-center text-sm text-sky-400 hover:text-sky-300"
              >
                View all tickets →
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
