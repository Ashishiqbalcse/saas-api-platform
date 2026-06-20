import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  timeout: 15000,
  headers: {
    "Content-Type": "application/json"
  }
});

api.interceptors.request.use((config) => {
  const key = localStorage.getItem("api_key");
  if (key) {
    config.headers.Authorization = `Bearer ${key}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    if (status === 401) {
      localStorage.removeItem("api_key");
      window.dispatchEvent(new Event("api:unauthorized"));
    }

    if (status === 429) {
      const retryAfter = Number(error.response?.headers?.["retry-after"] || 0);
      error.friendlyMessage = retryAfter
        ? `Rate limit exceeded. Retry in ${Math.ceil(retryAfter / 60)} minutes.`
        : "Rate limit exceeded.";
    }

    if (status === 403) {
      error.friendlyMessage =
        typeof error.response?.data?.detail === "string"
          ? error.response.data.detail
          : "This feature requires a higher plan.";
    }

    return Promise.reject(error);
  }
);

export default api;
