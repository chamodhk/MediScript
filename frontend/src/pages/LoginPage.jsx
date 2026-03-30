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
        requestError?.response?.data?.detail || "Login failed. Check your credentials.";
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto mt-16 max-w-[420px] p-4 text-white">
      <h1 className="mb-4 text-2xl font-semibold">MediScript Login</h1>
      <form onSubmit={handleSubmit}>
        <div className="mb-3">
          <label htmlFor="email" className="mb-1 block text-sm font-medium text-gray-200">
            Email
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            required
            className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 placeholder:text-gray-500 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40"
          />
        </div>

        <div className="mb-3">
          <label htmlFor="password" className="mb-1 block text-sm font-medium text-gray-200">
            Password
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="password"
            required
            className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 placeholder:text-gray-500 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40"
          />
        </div>

        {error ? (
          <p className="mb-3 text-sm text-red-400">{error}</p>
        ) : null}

        <button
          type="submit"
          disabled={loading}
          className="rounded-md bg-orange-600 px-4 py-2 font-medium text-white transition hover:bg-orange-500 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </div>
  );
}
