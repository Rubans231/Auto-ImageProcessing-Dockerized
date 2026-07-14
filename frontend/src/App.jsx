import { useEffect, useState, useCallback } from "react";
import Sidebar from "./components/Sidebar.jsx";
import SpecimenHeader from "./components/SpecimenHeader.jsx";
import CoreSample from "./components/CoreSample.jsx";
import Journal from "./components/Journal.jsx";
import QueryPanel from "./components/QueryPanel.jsx";
import StatusBar from "./components/StatusBar.jsx";
import Settings from "./components/Settings.jsx";
import SnapshotLogs from "./components/SnapshotLogs.jsx";
import Charts from "./components/Charts.jsx";
import DropIn from "./components/DropIn/DropIn.jsx";
import FileBrowser from "./components/FileBrowser.jsx";
import { api } from "./api.js";

// SSE tells us the moment something changes; this is just a safety net for
// if that connection silently drops (network blip, tab backgrounded, etc).
const FALLBACK_POLL_MS = 60000;

const TABS = [
  { id: "overview", label: "Overview" },
  { id: "logs", label: "Snapshot Logs" },
  { id: "graphs", label: "Graphs" },
  { id: "add", label: "Add Frames" },
  { id: "browse", label: "Browse Files" },
];

export default function App() {
  const [wings, setWings] = useState([]);
  const [selectedWing, setSelectedWing] = useState(null);
  const [summary, setSummary] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [history, setHistory] = useState([]);
  const [selectedLayer, setSelectedLayer] = useState(0);
  const [status, setStatus] = useState(null);
  const [health, setHealth] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [showSettings, setShowSettings] = useState(false);
  const [defaultInterval, setDefaultInterval] = useState(10);

  const refreshWings = useCallback(async () => {
    const data = await api.get("/wings");
    setWings(data);
    if (!selectedWing && data.length > 0) setSelectedWing(data[0].wing);
  }, [selectedWing]);

  const refreshWingDetail = useCallback(async (wing) => {
    if (!wing) return;
    const [s, t, h] = await Promise.all([
      api.get(`/wings/${wing}/summary`),
      api.get(`/wings/${wing}/timeline?limit=100`),
      api.get(`/wings/${wing}/history`),
    ]);
    setSummary(s);
    setTimeline(t);
    setHistory(h);
    setSelectedLayer(0);
  }, []);

  const refreshSystem = useCallback(async () => {
    const [s, h] = await Promise.all([
      api.get("/status").catch(() => null),
      api.get("/health").catch(() => null),
    ]);
    if (s) setStatus(s);
    if (h) setHealth(h);
  }, []);

  useEffect(() => {
    refreshWings();
    refreshSystem();
    api
      .get("/settings")
      .then((s) => setDefaultInterval(s.capture_interval_seconds))
      .catch(() => {});
    const id = setInterval(() => {
      refreshWings();
      refreshSystem();
    }, FALLBACK_POLL_MS);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    refreshWingDetail(selectedWing);
  }, [selectedWing, refreshWingDetail]);

  // Live updates: the API's SSE stream tells us when processed.jpg or
  // history.md actually changed for this wing, so we refetch only then
  // instead of polling everything on a fixed timer.
  useEffect(() => {
    if (!selectedWing) return;
    const unsubscribe = api.events(`/wings/${selectedWing}/events`, (msg) => {
      if (msg.type === "update") refreshWingDetail(selectedWing);
    });
    const fallback = setInterval(() => refreshWingDetail(selectedWing), FALLBACK_POLL_MS);
    return () => {
      unsubscribe();
      clearInterval(fallback);
    };
  }, [selectedWing, refreshWingDetail]);

  return (
    <div className="flex bg-basalt min-h-screen">
      <Sidebar wings={wings} selected={selectedWing} onSelect={setSelectedWing} />

      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex items-center justify-between border-b border-panel-raised px-6">
          <div className="flex gap-1">
            {TABS.map((t) => (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id)}
                className={`px-3 py-3 font-mono text-xs uppercase tracking-wider transition-colors ${
                  activeTab === t.id
                    ? "text-moss border-b-2 border-moss"
                    : "text-slate-fog hover:text-parchment"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
          <button
            onClick={() => setShowSettings(true)}
            className="font-mono text-xs text-slate-fog hover:text-parchment px-2"
            title="Settings"
          >
            ⚙ settings
          </button>
        </div>

        <div className="flex-1 min-h-0 overflow-y-auto">
          {activeTab === "overview" &&
            (selectedWing ? (
              <>
                <SpecimenHeader wing={selectedWing} summary={summary} />
                <div className="grid grid-cols-2 gap-4 p-6">
                  <CoreSample entries={timeline} selected={selectedLayer} onSelect={setSelectedLayer} />
                  <Journal entries={history} />
                </div>
                <div className="px-6 pb-6">
                  <QueryPanel wing={selectedWing} />
                </div>
              </>
            ) : (
              <div className="flex items-center justify-center p-12">
                <p className="font-mono text-sm text-slate-fog">
                  No wings monitored yet — add frames using the "Add Frames" tab.
                </p>
              </div>
            ))}

          {activeTab === "logs" && (
            <div className="p-6">
              <SnapshotLogs entries={timeline} />
            </div>
          )}

          {activeTab === "graphs" && (
            <div className="p-6">
              {selectedWing ? (
                <Charts entries={timeline} />
              ) : (
                <p className="font-mono text-sm text-slate-fog">Select a wing first.</p>
              )}
            </div>
          )}

          {activeTab === "add" && (
            <div className="p-6">
              <DropIn wings={wings} defaultInterval={defaultInterval} />
            </div>
          )}

          {activeTab === "browse" && (
            <div className="p-6">
              <FileBrowser />
            </div>
          )}
        </div>

        <StatusBar status={status} health={health} />
      </div>

      {showSettings && <Settings wing={selectedWing} onClose={() => setShowSettings(false)} />}
    </div>
  );
}
