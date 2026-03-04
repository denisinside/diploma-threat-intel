import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Server,
  ShieldAlert,
  Bug,
  Ticket,
  Bell,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { to: "/overview", icon: LayoutDashboard, label: "OVERVIEW" },
  { to: "/assets", icon: Server, label: "ASSETS" },
  { to: "/leaks", icon: ShieldAlert, label: "LEAKS" },
  { to: "/vulnerabilities", icon: Bug, label: "VULNERABILITIES" },
  { to: "/tickets", icon: Ticket, label: "TICKETS" },
  { to: "/subscriptions", icon: Bell, label: "SUBSCRIPTIONS" },
  { to: "/settings", icon: Settings, label: "SETTINGS" },
];

export function Sidebar() {
  return (
    <aside className="w-56 flex-shrink-0 glass-panel border-r border-slate-700/50 flex flex-col">
      <div className="p-4 border-b border-slate-700/50">
        <h1 className="text-xs font-semibold text-slate-400 tracking-wider">
          THREAT INTELLIGENCE
        </h1>
        <p className="text-sm font-medium text-slate-200">Monitoring System</p>
      </div>
      <nav className="flex-1 p-2 space-y-0.5">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                isActive
                  ? "bg-sky-500/20 text-tactical-sky border-l-2 border-tactical-sky"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
              )
            }
          >
            <Icon className="w-4 h-4 flex-shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
