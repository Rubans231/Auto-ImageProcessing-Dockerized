import { useEffect, useState } from "react";
import { api } from "../api.js";

const ROOTS = [
  { id: "categories", label: "categories/" },
  { id: "snapshots", label: "snapshots/" },
  { id: "workspace_input", label: "workspace/input/" },
];

function formatSize(bytes) {
  if (bytes == null) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function FileBrowser() {
  const [root, setRoot] = useState("categories");
  const [path, setPath] = useState("");
  const [entries, setEntries] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    setError("");
    api
      .get(`/browse?root=${root}&path=${encodeURIComponent(path)}`)
      .then((data) => setEntries(data.entries))
      .catch((err) => setError(err.message));
  }, [root, path]);

  function enterDir(name) {
    setPath((p) => (p ? `${p}/${name}` : name));
  }

  function goUp() {
    setPath((p) => p.split("/").slice(0, -1).join("/"));
  }

  function switchRoot(r) {
    setRoot(r);
    setPath("");
  }

  return (
    <div className="rounded-sm border border-panel-raised bg-panel p-4">
      <div className="flex gap-2 mb-3">
        {ROOTS.map((r) => (
          <button
            key={r.id}
            onClick={() => switchRoot(r.id)}
            className={`px-3 py-1.5 font-mono text-xs rounded-sm transition-colors ${
              root === r.id ? "bg-moss-dim text-parchment" : "text-slate-fog hover:text-parchment"
            }`}
          >
            {r.label}
          </button>
        ))}
      </div>

      <div className="font-mono text-[11px] text-slate-fog mb-2 flex items-center gap-2">
        <button onClick={goUp} disabled={!path} className="disabled:opacity-30 hover:text-parchment">
          ↑ up
        </button>
        <span>/{path}</span>
      </div>

      {error && <p className="font-mono text-xs text-rust mb-2">{error}</p>}

      <div className="border border-panel-raised rounded-sm max-h-80 overflow-y-auto">
        {entries.map((e) => (
          <div
            key={e.name}
            className="flex items-center justify-between px-3 py-1.5 border-b border-basalt/40 last:border-0 font-mono text-[11px]"
          >
            {e.is_dir ? (
              <button onClick={() => enterDir(e.name)} className="text-parchment hover:text-moss text-left">
                📁 {e.name}
              </button>
            ) : (
              <span className="text-parchment">📄 {e.name}</span>
            )}
            <div className="flex items-center gap-3 text-slate-fog">
              <span>{formatSize(e.size)}</span>
              {!e.is_dir && (
                <a
                  href={`/api/browse/download?root=${root}&path=${encodeURIComponent(
                    path ? `${path}/${e.name}` : e.name
                  )}`}
                  className="text-moss hover:text-parchment"
                >
                  download
                </a>
              )}
            </div>
          </div>
        ))}
        {entries.length === 0 && !error && (
          <p className="px-3 py-4 text-center font-mono text-xs text-slate-fog">Empty directory.</p>
        )}
      </div>
    </div>
  );
}
