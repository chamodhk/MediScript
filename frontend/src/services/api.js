import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("accessToken");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  // Preserve explicitly provided headers and browser-managed multipart/form data.
  if (
    !config.headers["Content-Type"] &&
    !(config.data instanceof FormData) &&
    !(config.data instanceof URLSearchParams)
  ) {
    config.headers["Content-Type"] = "application/json";
  }

  return config;
});

export default api;
