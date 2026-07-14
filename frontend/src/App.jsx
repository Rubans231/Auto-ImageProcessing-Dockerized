import { useEffect, useState, useCallback } from "react";
import Sidebar from "./components/Sidebar.jsx";
import SpecimenHeader from "./components/SpecimenHeader.jsx";
import CoreSample from "./components/CoreSample.jsx";
import Journal from "./components/Journal.jsx";
import QueryPanel from "./components/QueryPanel.jsx";
import StatusBar from "./components/StatusBar.jsx";

const POLL_MS = 15000;

export default function App() {
  const [wings, setWings] = useState([]);
  const [selectedWing, setSelectedWing] = useState(null);
  const [summary, setSummary] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [history, setHistory] = useState([]);
  const [selectedLayer, setSelectedLayer] = useState(0);
  const [status, setStatus] = useState(null);
  const [health, setHealth] = useState(null);

  const refreshWings = useCallback(async () => {
    const res = await fetch("/api/wings");
    const data = await res.json();
    setWings(data);
    if (!selectedWing && data.length > 0) setSelectedWing(data[0].wing);
  }, [selectedWing]);

  const refreshWingDetail = useCallback(async (wing) => {
    if (!wing) return;
    const [summaryRes, timelineRes, historyRes] = await Promise.all([
      fetch(`/api/wings/${wing}/summary`),
      fetch(`/api/wings/${wing}/timeline?limit=100`),
      fetch(`/api/wings/${wing}/history`),
    ]);
    setSummary(await summaryRes.json());
    setTimeline(await timelineRes.json());
    setHistory(await historyRes.json());
    setSelectedLayer(0);
  }, []);

  const refreshSystem = useCallback(async () => {
    const [statusRes, healthRes] = await Promise.all([
      fetch("/api/status").catch(() => null),
      fetch("/api/health").catch(() => null),
    ]);
    if (statusRes?.ok) setStatus(await statusRes.json());
    if (healthRes?.ok) setHealth(await healthRes.json());
  }, []);

  useEffect(() => {
    refreshWings();
    refreshSystem();
    const id = setInterval(() => {
      refreshWings();
      refreshSystem();
    }, POLL_MS);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    refreshWingDetail(selectedWing);
    const id = setInterval(() => refreshWingDetail(selectedWing), POLL_MS);
    return () => clearInterval(id);
  }, [selectedWing, refreshWingDetail]);

  return (
    <div className="flex bg-basalt min-h-screen">
      <Sidebar wings={wings} selected={selectedWing} onSelect={setSelectedWing} />

      <div className="flex-1 flex flex-col min-w-0">
        {selectedWing ? (
          <>
            <SpecimenHeader wing={selectedWing} summary={summary} />

            <div className="grid grid-cols-2 gap-4 p-6 flex-1 min-h-0">
              <CoreSample
                entries={timeline}
                selected={selectedLayer}
                onSelect={setSelectedLayer}
              />
              <Journal entries={history} />
            </div>

            <div className="px-6 pb-6">
              <QueryPanel wing={selectedWing} />
            </div>

            <StatusBar status={status} health={health} />
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <p className="font-mono text-sm text-slate-fog">
              No wings monitored yet — drop an image into a category folder to begin.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
