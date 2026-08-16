const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const token = localStorage.getItem('veritas_token');
  const headers = { ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  // Some endpoints return a file (blob), handle that in callers
  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) return res.json();
  return res;
}

export const api = {
  health: () => request("/api/health"),

  runDemo: () => request("/api/demo/run", { method: "GET" }),

  listProducts: () => request("/api/products"),

  getProduct: (id) => request(`/api/products/${encodeURIComponent(id)}`),

  ingest: (body) =>
    request("/api/ingest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),

  ingestUpload: (formData) =>
    request("/api/ingest/upload", { method: "POST", body: formData }),

  ingestDiscover: (body) =>
    request("/api/ingest/discover", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),

  reviewAttribute: (productId, payload) =>
    request(`/api/products/${encodeURIComponent(productId)}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  ask: (productId, q) =>
    request(`/api/products/${encodeURIComponent(productId)}/ask?q=${encodeURIComponent(q)}`),

  exportProduct: (productId, format) => {
    const token = localStorage.getItem('veritas_token');
    return fetch(`${API_BASE}/api/products/${encodeURIComponent(productId)}/export?format=${encodeURIComponent(format)}`, {
      headers: token ? { 'Authorization': `Bearer ${token}` } : {}
    });
  }
};
