import { useState } from "react";
import { SectionCard } from "@/components/ui/SectionCard";
import {
  useCompanyUsers,
  useRegisterAnalyst,
  useDeleteUser,
} from "@/features/team/hooks";

export function TeamPage() {
  const { data: users = [], isLoading } = useCompanyUsers();
  const registerAnalyst = useRegisterAnalyst();
  const deleteUser = useDeleteUser();
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");

  const analysts = users.filter((u) => u.role === "analyst");
  const admins = users.filter((u) => u.role === "admin");

  function handleAddAnalyst(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim() || !fullName.trim() || !password) return;
    registerAnalyst.mutate(
      { email: email.trim(), full_name: fullName.trim(), password },
      {
        onSuccess: () => {
          setEmail("");
          setFullName("");
          setPassword("");
        },
      }
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-slate-100">Team</h1>
      <SectionCard title="Analysts">
        <p className="text-sm text-slate-400 mb-4">Add analysts to your company. They can create, edit, and delete assets.</p>
        <form onSubmit={handleAddAnalyst} className="mb-4 flex flex-wrap gap-2">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email"
            className="px-3 py-2 bg-slate-800/50 border border-slate-600 rounded-md text-slate-100 text-sm"
            required
          />
          <input
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Full name"
            className="px-3 py-2 bg-slate-800/50 border border-slate-600 rounded-md text-slate-100 text-sm"
            required
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            minLength={8}
            className="px-3 py-2 bg-slate-800/50 border border-slate-600 rounded-md text-slate-100 text-sm"
            required
          />
          <button
            type="submit"
            disabled={registerAnalyst.isPending}
            className="px-4 py-2 rounded border border-tactical-sky/40 text-tactical-sky hover:bg-tactical-sky/15 text-sm disabled:opacity-50"
          >
            {registerAnalyst.isPending ? "Adding..." : "Add analyst"}
          </button>
        </form>
        {isLoading ? (
          <p className="text-slate-400">Loading...</p>
        ) : (
          <div className="space-y-2">
            {admins.map((u) => (
              <div
                key={u._id}
                className="flex items-center justify-between py-2 px-3 rounded bg-slate-800/30"
              >
                <div>
                  <span className="text-slate-200">{u.full_name}</span>
                  <span className="text-slate-500 ml-2">({u.email})</span>
                  <span className="ml-2 text-xs text-slate-500">admin</span>
                </div>
              </div>
            ))}
            {analysts.map((u) => (
              <div
                key={u._id}
                className="flex items-center justify-between py-2 px-3 rounded bg-slate-800/30"
              >
                <div>
                  <span className="text-slate-200">{u.full_name}</span>
                  <span className="text-slate-500 ml-2">({u.email})</span>
                  <span className="ml-2 text-xs text-slate-500">analyst</span>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    if (window.confirm(`Delete ${u.full_name}?`)) {
                      deleteUser.mutate(u._id);
                    }
                  }}
                  disabled={deleteUser.isPending}
                  className="text-xs text-red-300 hover:text-red-200 disabled:opacity-50"
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        )}
      </SectionCard>
    </div>
  );
}
