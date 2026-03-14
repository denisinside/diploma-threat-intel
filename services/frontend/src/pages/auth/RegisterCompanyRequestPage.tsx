import { useState } from "react";
import { Link } from "react-router-dom";
import { apiClient } from "@/lib/api";

export function RegisterCompanyRequestPage() {
  const [name, setName] = useState("");
  const [domain, setDomain] = useState("");
  const [adminEmail, setAdminEmail] = useState("");
  const [adminFullName, setAdminFullName] = useState("");
  const [adminPassword, setAdminPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await apiClient.post("/auth/company-registration-request", {
        name: name.trim(),
        domain: domain.trim(),
        admin_email: adminEmail.trim(),
        admin_full_name: adminFullName.trim(),
        admin_password: adminPassword,
      });
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit request");
    }
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 p-4">
        <div className="glass-panel w-full max-w-md p-8 text-center">
          <h1 className="text-xl font-semibold text-emerald-300 mb-2">Request submitted</h1>
          <p className="text-sm text-slate-400 mb-6">
            Your company registration request has been sent. A system administrator will review it and notify you once approved.
          </p>
          <Link
            to="/login"
            className="inline-block px-4 py-2 rounded border border-tactical-sky/40 text-tactical-sky hover:bg-tactical-sky/15"
          >
            Back to login
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 p-4">
      <div className="glass-panel w-full max-w-md p-8">
        <h1 className="text-xl font-semibold text-slate-100 mb-1">Request company registration</h1>
        <p className="text-sm text-slate-400 mb-6">Submit a request for approval by the system administrator</p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1">Company name</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 bg-slate-800/50 border border-slate-600 rounded-md text-slate-100"
              required
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Company domain (e.g. example.com)</label>
            <input
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              placeholder="example.com"
              className="w-full px-3 py-2 bg-slate-800/50 border border-slate-600 rounded-md text-slate-100"
              required
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Admin email</label>
            <input
              type="email"
              value={adminEmail}
              onChange={(e) => setAdminEmail(e.target.value)}
              className="w-full px-3 py-2 bg-slate-800/50 border border-slate-600 rounded-md text-slate-100"
              required
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Admin full name</label>
            <input
              value={adminFullName}
              onChange={(e) => setAdminFullName(e.target.value)}
              className="w-full px-3 py-2 bg-slate-800/50 border border-slate-600 rounded-md text-slate-100"
              required
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Admin password</label>
            <input
              type="password"
              value={adminPassword}
              onChange={(e) => setAdminPassword(e.target.value)}
              minLength={8}
              className="w-full px-3 py-2 bg-slate-800/50 border border-slate-600 rounded-md text-slate-100"
              required
            />
          </div>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <button
            type="submit"
            className="w-full py-2 px-4 bg-tactical-sky/20 text-tactical-sky border border-tactical-sky/50 rounded-md hover:bg-tactical-sky/30 font-medium"
          >
            Submit request
          </button>
        </form>
        <Link to="/login" className="mt-4 block text-center text-sm text-slate-400 hover:text-slate-300">
          Back to login
        </Link>
      </div>
    </div>
  );
}
