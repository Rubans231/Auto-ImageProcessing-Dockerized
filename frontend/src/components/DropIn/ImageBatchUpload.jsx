import { useState, useCallback } from "react";
import { api } from "../../api.js";

let nextId = 0;

async function runQueue(items, concurrency, worker) {
  let index = 0;
  async function step() {
    const current = index++;
    if (current >= items.length) return;
    await worker(items[current]);
    await step();
  }
  await Promise.all(Array.from({ length: concurrency }, step));
}

export default function ImageBatchUpload({ wing, room }) {
  const [queue, setQueue] = useState([]);
  const [running, setRunning] = useState(false);

  const addFiles = useCallback((fileList) => {
    const items = Array.from(fileList).map((file) => ({
      id: nextId++,
      file,
      status: "pending",
      error: null,
    }));
    setQueue((q) => [...q, ...items]);
  }, []);

  function updateItem(id, patch) {
    setQueue((q) => q.map((item) => (item.id === id ? { ...item, ...patch } : item)));
  }

  async function startUpload() {
    if (running) return;
    setRunning(true);
    // Re-includes "error" items too, so re-clicking "Start queue" acts as a retry.
    const toUpload = queue.filter((i) => i.status === "pending" || i.status === "error");
    await runQueue(toUpload, 2, async (item) => {
      updateItem(item.id, { status: "uploading", error: null });
      try {
        const form = new FormData();
        form.append("files", item.file);
        const params = room ? `?room=${encodeURIComponent(room)}` : "";
        const res = await api.upload(`/wings/${wing}/upload${params}`, form);
        const result = res.results?.[0];
        if (result?.status === "rejected") {
          updateItem(item.id, { status: "error", error: result.reason });
        } else {
          updateItem(item.id, { status: "done" });
        }
      } catch (err) {
        updateItem(item.id, { status: "error", error: err.message });
      }
    });
    setRunning(false);
  }

  function clearDone() {
    setQueue((q) => q.filter((i) => i.status !== "done"));
  }

  const counts = queue.reduce((acc, i) => ({ ...acc, [i.status]: (acc[i.status] || 0) + 1 }), {});

  return (
    <div>
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          addFiles(e.dataTransfer.files);
        }}
        className="border-2 border-dashed border-panel-raised rounded-sm p-8 text-center"
      >
        <p className="font-mono text-sm text-slate-fog mb-2">Drag images here, or</p>
        <label className="inline-block px-4 py-2 bg-moss-dim text-parchment text-sm rounded-sm cursor-pointer hover:bg-moss transition-colors">
          Choose files
          <input
            type="file"
            multiple
            accept="image/jpeg,image/png,image/webp"
            className="hidden"
            onChange={(e) => addFiles(e.target.files)}
          />
        </label>
      </div>

      {queue.length > 0 && (
        <div className="mt-4">
          <div className="flex items-center justify-between mb-2">
            <span className="font-mono text-[11px] text-slate-fog">
              {counts.done || 0} done · {counts.uploading || 0} uploading · {counts.pending || 0} queued
              {counts.error ? ` · ${counts.error} failed` : ""}
            </span>
            <div className="flex gap-2">
              <button
                onClick={startUpload}
                disabled={running}
                className="px-3 py-1.5 bg-moss-dim text-parchment text-xs rounded-sm hover:bg-moss disabled:opacity-50 transition-colors"
              >
                {running ? "Uploading…" : "Start queue"}
              </button>
              <button
                onClick={clearDone}
                className="px-3 py-1.5 text-xs text-slate-fog hover:text-parchment transition-colors"
              >
                Clear done
              </button>
            </div>
          </div>
          <div className="max-h-64 overflow-y-auto border border-panel-raised rounded-sm">
            {queue.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between px-3 py-1.5 border-b border-basalt/40 last:border-0 font-mono text-[11px]"
              >
                <span className="truncate text-parchment">{item.file.name}</span>
                <span
                  className={
                    item.status === "done"
                      ? "text-moss"
                      : item.status === "error"
                      ? "text-rust"
                      : item.status === "uploading"
                      ? "text-parchment"
                      : "text-slate-fog"
                  }
                >
                  {item.status === "error" ? item.error : item.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
