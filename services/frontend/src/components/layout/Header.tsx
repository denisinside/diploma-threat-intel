import { LogOut, Settings, User } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { NotificationDropdown } from "./NotificationDropdown";

export function Header() {
  const { session, logout } = useAuth();

  return (
    <header className="relative z-20 h-14 flex-shrink-0 glass-panel rounded-none border-b border-slate-700/50 flex items-center justify-between px-6">
      <h2 className="text-lg font-semibold text-slate-200 tracking-wide">
      </h2>
      <div className="flex items-center gap-4">
        <NotificationDropdown companyId={session?.user?.company_id} />
        <button
          type="button"
          className="p-2 text-slate-400 hover:text-slate-200 rounded-md hover:bg-slate-800/50"
          aria-label="Settings"
        >
          <Settings className="w-5 h-5" />
        </button>
        <button
          type="button"
          className="flex items-center gap-2 p-2 text-slate-400 hover:text-slate-200 rounded-md hover:bg-slate-800/50"
          aria-label="User menu"
        >
          <User className="w-5 h-5" />
          <span className="text-sm">{session?.user?.full_name ?? "User"}</span>
        </button>
        <button
          type="button"
          onClick={logout}
          className="flex items-center gap-2 p-2 text-slate-400 hover:text-red-300 rounded-md hover:bg-red-950/20"
          aria-label="Sign out"
        >
          <LogOut className="w-5 h-5" />
        </button>
      </div>
    </header>
  );
}
