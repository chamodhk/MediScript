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

// Handle token expiration (401 errors)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem("accessToken");
      localStorage.removeItem("userRole");
      window.location.href = "/";
    }
    return Promise.reject(error);
  }
);

export default api;
