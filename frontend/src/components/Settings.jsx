import { useEffect, useState } from "react";
import { api } from "../api.js";

export default function Settings({ wing, onClose }) {
  const [globalInterval, setGlobalInterval] = useState(10);
  const [wingInterval, setWingInterval] = useState(null);
  const [useOverride, setUseOverride] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/settings").then((s) => setGlobalInterval(s.capture_interval_seconds));
    if (wing) {
      api.get(`/wings/${wing}/settings`).then((s) => setWingInterval(s.capture_interval_seconds));
    }
  }, [wing]);

  async function handleSave() {
    setSaving(true);
    setError("");
    try {
      await api.put("/settings", { capture_interval_seconds: Number(globalInterval) });
      if (wing && useOverride) {
        await api.put(`/wings/${wing}/settings`, {
          capture_interval_seconds: Number(wingInterval),
        });
      }
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-panel border border-panel-raised rounded-sm p-6 w-96">
        <h3 className="font-display text-xl text-parchment mb-4">Settings</h3>

        <label className="block font-mono text-[11px] uppercase tracking-wider text-slate-fog mb-1">
          Default capture interval (seconds)
        </label>
        <p className="font-mono text-[10px] text-slate-fog mb-2">
          How often the browser camera and video frame extraction pull a new frame, unless a wing overrides it below.
        </p>
        <input
          type="number"
          min="1"
          step="1"
          value={globalInterval}
          onChange={(e) => setGlobalInterval(e.target.value)}
          className="w-full bg-basalt border border-panel-raised rounded-sm px-3 py-2 text-sm text-parchment mb-4"
        />

        {wing && (
          <>
            <label className="flex items-center gap-2 font-mono text-[11px] text-slate-fog mb-2">
              <input
                type="checkbox"
                checked={useOverride}
                onChange={(e) => setUseOverride(e.target.checked)}
              />
              Override for <span className="text-parchment">{wing}</span> specifically
            </label>
            {useOverride && (
              <input
                type="number"
                min="1"
                step="1"
                value={wingInterval ?? globalInterval}
                onChange={(e) => setWingInterval(e.target.value)}
                className="w-full bg-basalt border border-panel-raised rounded-sm px-3 py-2 text-sm text-parchment mb-4"
              />
            )}
          </>
        )}

        {error && <p className="font-mono text-xs text-rust mb-3">{error}</p>}

        <div className="flex justify-end gap-2 mt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-sm text-sm text-slate-fog hover:text-parchment transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 rounded-sm bg-moss-dim text-parchment text-sm font-medium hover:bg-moss disabled:opacity-50 transition-colors"
          >
            {saving ? "Saving…" : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}
