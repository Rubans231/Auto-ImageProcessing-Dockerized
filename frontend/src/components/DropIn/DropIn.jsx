import { useState } from "react";
import ImageBatchUpload from "./ImageBatchUpload.jsx";
import VideoUpload from "./VideoUpload.jsx";
import CameraCapture from "./CameraCapture.jsx";

const TABS = [
  { id: "images", label: "Images" },
  { id: "video", label: "Video" },
  { id: "camera", label: "Camera" },
];

export default function DropIn({ wings, defaultInterval }) {
  const [mode, setMode] = useState(wings.length > 0 ? "existing" : "new");
  const [existingWing, setExistingWing] = useState(wings[0]?.wing || "");
  const [newWing, setNewWing] = useState("");
  const [room, setRoom] = useState("");
  const [activeTab, setActiveTab] = useState("images");

  const targetWing = mode === "existing" ? existingWing : newWing.trim();
  const canProceed = targetWing.length > 0;

  return (
    <div className="space-y-4">
      <div className="rounded-sm border border-panel-raised bg-panel p-4">
        <h3 className="font-mono text-[11px] uppercase tracking-wider text-slate-fog mb-3">
          Add frames to
        </h3>
        <div className="flex gap-4 mb-3 font-mono text-xs text-parchment">
          <label className="flex items-center gap-1.5">
            <input
              type="radio"
              checked={mode === "existing"}
              onChange={() => setMode("existing")}
              disabled={wings.length === 0}
            />
            Existing category
          </label>
          <label className="flex items-center gap-1.5">
            <input type="radio" checked={mode === "new"} onChange={() => setMode("new")} />
            New category
          </label>
        </div>

        <div className="flex gap-3">
          {mode === "existing" ? (
            <select
              value={existingWing}
              onChange={(e) => setExistingWing(e.target.value)}
              className="bg-basalt border border-panel-raised rounded-sm px-3 py-2 text-sm text-parchment"
            >
              {wings.map((w) => (
                <option key={w.wing} value={w.wing}>
                  {w.wing}
                </option>
              ))}
            </select>
          ) : (
            <input
              type="text"
              placeholder="new-category-name"
              value={newWing}
              onChange={(e) => setNewWing(e.target.value)}
              className="bg-basalt border border-panel-raised rounded-sm px-3 py-2 text-sm text-parchment placeholder:text-slate-fog"
            />
          )}
          <input
            type="text"
            placeholder="room (optional)"
            value={room}
            onChange={(e) => setRoom(e.target.value)}
            className="bg-basalt border border-panel-raised rounded-sm px-3 py-2 text-sm text-parchment placeholder:text-slate-fog"
          />
        </div>
      </div>

      {!canProceed ? (
        <p className="font-mono text-xs text-slate-fog px-1">
          Choose or name a category above to start adding frames.
        </p>
      ) : (
        <div className="rounded-sm border border-panel-raised bg-panel p-4">
          <div className="flex gap-1 mb-4 border-b border-panel-raised">
            {TABS.map((t) => (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id)}
                className={`px-3 py-2 font-mono text-xs uppercase tracking-wider transition-colors ${
                  activeTab === t.id
                    ? "text-moss border-b-2 border-moss"
                    : "text-slate-fog hover:text-parchment"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          {activeTab === "images" && <ImageBatchUpload wing={targetWing} room={room || null} />}
          {activeTab === "video" && (
            <VideoUpload wing={targetWing} room={room || null} defaultInterval={defaultInterval} />
          )}
          {activeTab === "camera" && (
            <CameraCapture wing={targetWing} room={room || null} defaultInterval={defaultInterval} />
          )}
        </div>
      )}
    </div>
  );
}
