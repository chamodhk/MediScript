import { useState } from "react";
import { useNavigate } from "react-router";

import api from "../services/api";

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const body = new URLSearchParams();
      body.append("username", email.trim());
      body.append("password", password);

      const { data } = await api.post("/auth/login", body, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });

      localStorage.setItem("accessToken", data.access_token);
      localStorage.setItem("userRole", data.role);
      navigate(data.redirectPath || "/", { replace: true });
    } catch (requestError) {
      const detail =
        requestError?.response?.data?.detail ||
        "Login failed. Check your credentials.";
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-gradient-to-br from-[#e6f4f7] via-[#f4fbfd] to-[#eef6f2] px-4 py-10 text-slate-800">
      <div className="pointer-events-none absolute -left-20 -top-20 h-72 w-72 rounded-full bg-[#b8e5ef]/60 blur-3xl" />
      <div className="pointer-events-none absolute -right-24 -bottom-16 h-80 w-80 rounded-full bg-[#c6efe2]/60 blur-3xl" />

      <div className="relative w-full max-w-[430px] rounded-3xl border border-slate-200/70 bg-white/90 p-8 shadow-[0_20px_50px_-20px_rgba(2,85,103,0.35)] backdrop-blur">
        <div className="mb-7">
          <p className="mb-2 inline-flex items-center rounded-full border border-[#00687f]/20 bg-[#00687f]/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-[#025567]">
            Secure Access
          </p>
          <h1 className="text-3xl font-bold leading-tight text-[#08263e]">
            Welcome back to MediScript
          </h1>
          <p className="mt-2 text-sm text-slate-600">
            Sign in to continue to your MediScript workspace.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="email"
              className="mb-1.5 block text-sm font-medium text-slate-700"
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-slate-900 placeholder:text-slate-400 transition focus:border-[#00687f] focus:outline-none focus:ring-4 focus:ring-[#00687f]/15"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="mb-1.5 block text-sm font-medium text-slate-700"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
              className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-slate-900 placeholder:text-slate-400 transition focus:border-[#00687f] focus:outline-none focus:ring-4 focus:ring-[#00687f]/15"
            />
          </div>

          {error ? (
            <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </p>
          ) : null}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-[#e75424] px-4 py-2.5 font-semibold text-white transition hover:bg-[#cf491d] focus:outline-none focus:ring-4 focus:ring-[#e75424]/25 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}
