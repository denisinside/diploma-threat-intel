import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiClient } from "@/lib/api";
import { setSession } from "@/lib/session";
import type { LoginResponse } from "@/types";

export function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
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

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 p-4">
      <div className="glass-panel w-full max-w-md p-8">
        <h1 className="text-xl font-semibold text-slate-100 mb-1">C.L.E.A.R.</h1>
        <p className="text-sm text-slate-400 mb-6">Corporate Leak & Exploit Alert Radar</p>
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
          <button
            type="submit"
            className="w-full py-2 px-4 bg-tactical-sky/20 text-tactical-sky border border-tactical-sky/50 rounded-md hover:bg-tactical-sky/30 font-medium"
          >
            Sign in
          </button>
        </form>
        <Link
          to="/register-company-request"
          className="mt-4 block text-center text-sm text-tactical-amber hover:text-amber-300"
        >
          Request company registration
        </Link>
      </div>
    </div>
  );
}
