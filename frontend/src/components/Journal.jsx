export default function Journal({ entries }) {
  return (
    <div className="flex flex-col h-full">
      <h3 className="font-mono text-[11px] uppercase tracking-wider text-slate-fog px-1 mb-2">
        Journal
      </h3>
      <div className="flex-1 overflow-y-auto rounded-sm border border-panel-raised bg-panel p-3 space-y-3">
        {entries.length === 0 && (
          <p className="font-mono text-xs text-slate-fog">
            No timelapse entries logged yet.
          </p>
        )}
        {entries.map((e) => (
          <div key={e.timestamp} className="pb-3 border-b border-panel-raised last:border-0">
            <div className="font-mono text-[10px] text-moss">{e.timestamp}</div>
            <p className="text-sm text-parchment mt-1 leading-relaxed">{e.text}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
