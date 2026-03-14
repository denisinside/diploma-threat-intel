import { SectionCard } from "@/components/ui/SectionCard";
import { useAuth } from "@/hooks/useAuth";

export function SettingsPage() {
  const { session, logout } = useAuth();

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-slate-100">Settings</h1>
      <SectionCard title="User Profile">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
          <p className="text-slate-400">
            Name: <span className="text-slate-100">{session?.user?.full_name ?? "—"}</span>
          </p>
          <p className="text-slate-400">
            Email: <span className="text-slate-100">{session?.user?.email ?? "—"}</span>
          </p>
          <p className="text-slate-400">
            Role: <span className="text-slate-100">{session?.user?.role ?? "—"}</span>
          </p>
          <p className="text-slate-400">
            Company ID: <span className="text-slate-100">{session?.user?.company_id ?? "—"}</span>
          </p>
        </div>
        <button
          type="button"
          onClick={logout}
          className="mt-4 px-4 py-2 rounded border border-red-500/40 text-red-300 hover:bg-red-950/30"
        >
          Sign out
        </button>
      </SectionCard>
    </div>
  );
}
