export default function SnapshotLogs({ entries }) {
  return (
    <div className="rounded-sm border border-panel-raised overflow-hidden">
      <table className="w-full text-left">
        <thead>
          <tr className="bg-panel-raised font-mono text-[10px] uppercase tracking-wider text-slate-fog">
            <th className="px-3 py-2">Time</th>
            <th className="px-3 py-2">Status</th>
            <th className="px-3 py-2">Humans</th>
            <th className="px-3 py-2">Novel objects</th>
            <th className="px-3 py-2">Missing</th>
            <th className="px-3 py-2">Log</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((e) => (
            <tr
              key={`${e.date}-${e.time}`}
              className="border-t border-panel-raised bg-panel hover:bg-panel-raised/60"
            >
              <td className="px-3 py-2 font-mono text-[11px] text-parchment whitespace-nowrap">
                {e.date} {e.time.replaceAll("-", ":")}
              </td>
              <td className="px-3 py-2">
                <span
                  className={`font-mono text-[10px] uppercase ${
                    e.drift_detected ? "text-rust" : "text-moss"
                  }`}
                >
                  {e.drift_detected ? "drift" : "stable"}
                </span>
              </td>
              <td className="px-3 py-2 font-mono text-[11px] text-parchment">{e.human_count}</td>
              <td className="px-3 py-2 font-mono text-[10px] text-slate-fog">
                {e.novel_objects?.length ? e.novel_objects.join(", ") : "—"}
              </td>
              <td className="px-3 py-2 font-mono text-[10px] text-slate-fog">
                {e.missing_objects?.length ? e.missing_objects.join(", ") : "—"}
              </td>
              <td
                className="px-3 py-2 font-mono text-[11px] text-slate-fog max-w-md truncate"
                title={e.detailed_log}
              >
                {e.detailed_log}
              </td>
            </tr>
          ))}
          {entries.length === 0 && (
            <tr>
              <td colSpan={6} className="px-3 py-6 text-center font-mono text-xs text-slate-fog">
                No snapshots recorded for this wing yet.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
