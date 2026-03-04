import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiClient } from "@/lib/api";
import { setSession } from "@/lib/session";
import type { LoginResponse } from "@/types";

export function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [companyDomain, setCompanyDomain] = useState("");
  const [showBootstrap, setShowBootstrap] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSuccess("");
    try {
      const res = await apiClient.post<LoginResponse>("/auth/login", {
        email,
        password,
      });
      setSession(res.access_token, res.user ?? null);
      navigate("/overview", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    }
  }

  async function handleBootstrap(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setSuccess("");
    if (!fullName.trim() || !companyName.trim() || !companyDomain.trim() || !email.trim() || !password.trim()) {
      setError("Fill all bootstrap fields.");
      return;
    }
    try {
      const company = await apiClient.post<{ _id: string }>("/auth/register-company", {
        name: companyName.trim(),
        domain: companyDomain.trim(),
        subscription_plan: "free",
      });

      await apiClient.post("/auth/register", {
        email: email.trim(),
        password,
        full_name: fullName.trim(),
        company_id: company._id,
      });

      const loginRes = await apiClient.post<LoginResponse>("/auth/login", {
        email: email.trim(),
        password,
      });
      setSession(loginRes.access_token, loginRes.user ?? null);
      setSuccess("Bootstrap admin created and logged in.");
      navigate("/overview", { replace: true });
    } catch (bootstrapError) {
      setError(bootstrapError instanceof Error ? bootstrapError.message : "Failed to bootstrap admin.");
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 p-4">
      <div className="glass-panel w-full max-w-md p-8">
        <h1 className="text-xl font-semibold text-slate-100 mb-6">
          Threat Intelligence Monitoring System
        </h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm text-slate-400 mb-1">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 bg-slate-800/50 border border-slate-600 rounded-md text-slate-100 focus:border-tactical-sky focus:ring-1 focus:ring-tactical-sky"
              required
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-sm text-slate-400 mb-1">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 bg-slate-800/50 border border-slate-600 rounded-md text-slate-100 focus:border-tactical-sky focus:ring-1 focus:ring-tactical-sky"
              required
            />
          </div>
          {error && <p className="text-sm text-red-400">{error}</p>}
          {success && <p className="text-sm text-emerald-400">{success}</p>}
          <button
            type="submit"
            className="w-full py-2 px-4 bg-tactical-sky/20 text-tactical-sky border border-tactical-sky/50 rounded-md hover:bg-tactical-sky/30 font-medium"
          >
            Sign in
          </button>
        </form>
        <button
          type="button"
          onClick={() => setShowBootstrap((prev) => !prev)}
          className="mt-4 text-xs text-tactical-amber hover:text-amber-300"
        >
          {showBootstrap ? "Hide first-admin setup" : "No users yet? Create first admin"}
        </button>

        {showBootstrap ? (
          <form onSubmit={handleBootstrap} className="mt-4 space-y-3 border-t border-slate-700/40 pt-4">
            <input
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
              placeholder="Full name"
              className="w-full px-3 py-2 bg-slate-800/50 border border-slate-600 rounded-md text-slate-100 text-sm"
            />
            <input
              value={companyName}
              onChange={(event) => setCompanyName(event.target.value)}
              placeholder="Company name"
              className="w-full px-3 py-2 bg-slate-800/50 border border-slate-600 rounded-md text-slate-100 text-sm"
            />
            <input
              value={companyDomain}
              onChange={(event) => setCompanyDomain(event.target.value)}
              placeholder="Company domain (example.com)"
              className="w-full px-3 py-2 bg-slate-800/50 border border-slate-600 rounded-md text-slate-100 text-sm"
            />
            <button
              type="submit"
              className="w-full py-2 px-4 bg-tactical-amber/20 text-tactical-amber border border-tactical-amber/40 rounded-md hover:bg-tactical-amber/30 text-sm"
            >
              Create first admin
            </button>
          </form>
        ) : null}
      </div>
    </div>
  );
}
