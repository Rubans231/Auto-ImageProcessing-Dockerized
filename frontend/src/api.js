const BASE = "/api";

async function handle(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export const api = {
  get: (path) => fetch(`${BASE}${path}`).then(handle),

  put: (path, body) =>
    fetch(`${BASE}${path}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(handle),

  post: (path, body) =>
    fetch(`${BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(handle),

  upload: (path, formData) =>
    fetch(`${BASE}${path}`, { method: "POST", body: formData }).then(handle),

  events: (path, onMessage) => {
    const source = new EventSource(`${BASE}${path}`);
    source.onmessage = (e) => {
      try {
        onMessage(JSON.parse(e.data));
      } catch {
        // keep-alive comments and malformed frames are just ignored
      }
    };
    return () => source.close();
  },
};
