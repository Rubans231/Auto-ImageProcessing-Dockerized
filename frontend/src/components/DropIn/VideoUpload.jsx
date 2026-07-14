import { useState } from "react";
import { api } from "../../api.js";

export default function VideoUpload({ wing, room, defaultInterval }) {
  const [file, setFile] = useState(null);
  const [mode, setMode] = useState("interval");
  const [intervalSeconds, setIntervalSeconds] = useState(defaultInterval || 10);
  const [status, setStatus] = useState(null);
  const [uploading, setUploading] = useState(false);

  function handleFile(f) {
    setFile(f);
    setStatus(null);
  }

  async function handleSubmit() {
    if (!file) return;
    setUploading(true);
    setStatus(null);
    try {
      const form = new FormData();
      form.append("file", file);
      form.append("extraction_mode", mode);
      form.append("interval_seconds", String(intervalSeconds));
      const params = room ? `?room=${encodeURIComponent(room)}` : "";
      const res = await api.upload(`/wings/${wing}/upload-video${params}`, form);
      setStatus({
        ok: true,
        message: `Extracted ${res.frames_extracted} frames — now queued for processing.`,
      });
      setFile(null);
    } catch (err) {
      setStatus({ ok: false, message: err.message });
    } finally {
      setUploading(false);
    }
  }

  return (
    <div>
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          const f = e.dataTransfer.files?.[0];
          if (f) handleFile(f);
        }}
        className="border-2 border-dashed border-panel-raised rounded-sm p-8 text-center"
      >
        {file ? (
          <p className="font-mono text-sm text-parchment">{file.name}</p>
        ) : (
          <>
            <p className="font-mono text-sm text-slate-fog mb-2">Drag a video here, or</p>
            <label className="inline-block px-4 py-2 bg-moss-dim text-parchment text-sm rounded-sm cursor-pointer hover:bg-moss transition-colors">
              Choose a video
              <input
                type="file"
                accept="video/mp4,video/quicktime,video/x-matroska,video/webm,video/x-msvideo"
                className="hidden"
                onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
              />
            </label>
          </>
        )}
      </div>

      {file && (
        <div className="mt-4 space-y-3">
          <div>
            <label className="font-mono text-[11px] uppercase tracking-wider text-slate-fog block mb-1">
              How should frames be extracted?
            </label>
            <div className="flex gap-4 font-mono text-xs text-parchment">
              <label className="flex items-center gap-1.5">
                <input type="radio" checked={mode === "interval"} onChange={() => setMode("interval")} />
                Every N seconds
              </label>
              <label className="flex items-center gap-1.5">
                <input
                  type="radio"
                  checked={mode === "every_frame"}
                  onChange={() => setMode("every_frame")}
                />
                Every frame
              </label>
            </div>
          </div>
          {mode === "interval" && (
            <input
              type="number"
              min="1"
              value={intervalSeconds}
              onChange={(e) => setIntervalSeconds(Number(e.target.value))}
              className="w-32 bg-basalt border border-panel-raised rounded-sm px-3 py-1.5 text-sm text-parchment"
            />
          )}
          <button
            onClick={handleSubmit}
            disabled={uploading}
            className="px-4 py-2 bg-moss-dim text-parchment text-sm rounded-sm hover:bg-moss disabled:opacity-50 transition-colors"
          >
            {uploading ? "Extracting…" : "Extract & queue frames"}
          </button>
        </div>
      )}

      {status && (
        <p className={`font-mono text-xs mt-3 ${status.ok ? "text-moss" : "text-rust"}`}>
          {status.message}
        </p>
      )}
    </div>
  );
}
