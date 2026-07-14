import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";

export default function Charts({ entries }) {
  const chronological = [...entries].reverse(); // entries arrive newest-first
  const data = chronological.map((e) => ({
    label: `${e.date} ${e.time.replaceAll("-", ":")}`,
    drift: e.drift_detected ? 1 : 0,
    humans: e.human_count,
  }));

  const tooltipStyle = {
    contentStyle: { background: "#1C2226", border: "1px solid #232A2E", fontSize: 11 },
    labelStyle: { color: "#8B948E" },
  };

  return (
    <div className="grid grid-cols-2 gap-4">
      <div className="rounded-sm border border-panel-raised bg-panel p-4">
        <h4 className="font-mono text-[11px] uppercase tracking-wider text-slate-fog mb-3">
          Drift over time
        </h4>
        {data.length === 0 ? (
          <p className="font-mono text-xs text-slate-fog">No data yet.</p>
        ) : (
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={data}>
              <CartesianGrid stroke="#232A2E" strokeDasharray="3 3" />
              <XAxis dataKey="label" hide />
              <YAxis domain={[0, 1]} ticks={[0, 1]} tick={{ fill: "#8B948E", fontSize: 10 }} />
              <Tooltip {...tooltipStyle} />
              <Bar dataKey="drift" fill="#C1693B" />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="rounded-sm border border-panel-raised bg-panel p-4">
        <h4 className="font-mono text-[11px] uppercase tracking-wider text-slate-fog mb-3">
          People detected over time
        </h4>
        {data.length === 0 ? (
          <p className="font-mono text-xs text-slate-fog">No data yet.</p>
        ) : (
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={data}>
              <CartesianGrid stroke="#232A2E" strokeDasharray="3 3" />
              <XAxis dataKey="label" hide />
              <YAxis tick={{ fill: "#8B948E", fontSize: 10 }} allowDecimals={false} />
              <Tooltip {...tooltipStyle} />
              <Line type="monotone" dataKey="humans" stroke="#7C9473" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
