export default function CoreSample({ entries, selected, onSelect }) {
  return (
    <div className="flex flex-col h-full">
      <h3 className="font-mono text-[11px] uppercase tracking-wider text-slate-fog px-1 mb-2">
        Core sample — {entries.length} layers, newest on top
      </h3>
      <div className="flex-1 overflow-y-auto rounded-sm border border-panel-raised">
        {entries.length === 0 && (
          <p className="font-mono text-xs text-slate-fog p-4">
            No snapshots recorded for this wing yet.
          </p>
        )}
        {entries.map((e, i) => {
          const isSelected = selected === i;
          return (
            <button
              key={`${e.date}-${e.time}`}
              onClick={() => onSelect(i)}
              className={`core-layer w-full flex items-center gap-3 px-3 py-2.5 text-left border-b border-basalt/40 transition-colors ${
                e.drift_detected ? "bg-rust-dim/40" : "bg-moss-dim/25"
              } ${isSelected ? "ring-1 ring-inset ring-parchment/40" : "hover:brightness-125"}`}
            >
              {e.image_url && (
                <img
                  src={e.image_url}
                  alt=""
                  className="w-10 h-10 object-cover rounded-sm shrink-0 border border-panel-raised"
                />
              )}
              <div className="min-w-0">
                <div className="font-mono text-[11px] text-parchment">
                  {e.date} <span className="text-slate-fog">{e.time.replaceAll("-", ":")}</span>
                </div>
                <div className="font-mono text-[10px] text-slate-fog truncate">
                  {e.drift_detected ? "drift detected" : "stable"}
                  {e.human_count > 0 ? ` · ${e.human_count} people` : ""}
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
