function timeAgo(iso) {
  if (!iso) return "no frames yet";
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.round(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.round(hours / 24)}d ago`;
}

export default function Sidebar({ wings, selected, onSelect }) {
  return (
    <aside className="w-64 shrink-0 border-r border-panel-raised bg-panel h-screen overflow-y-auto">
      <div className="px-5 pt-6 pb-4">
        <h1 className="font-display text-2xl tracking-tight text-parchment">
          Field Log
        </h1>
        <p className="font-mono text-[11px] text-slate-fog mt-1">
          {wings.length} monitored {wings.length === 1 ? "wing" : "wings"}
        </p>
      </div>
      <nav className="px-2 pb-6">
        {wings.map((w) => {
          const isSelected = w.wing === selected;
          const dotColor =
            w.drift_detected === true
              ? "bg-rust"
              : w.drift_detected === false
              ? "bg-moss"
              : "bg-slate-fog";
          return (
            <button
              key={w.wing}
              onClick={() => onSelect(w.wing)}
              className={`w-full text-left px-3 py-2.5 rounded-sm mb-1 transition-colors ${
                isSelected
                  ? "bg-panel-raised border-l-2 border-moss"
                  : "border-l-2 border-transparent hover:bg-panel-raised/60"
              }`}
            >
              <div className="flex items-center gap-2">
                <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />
                <span className="font-mono text-sm text-parchment">{w.wing}</span>
              </div>
              <div className="font-mono text-[10px] text-slate-fog pl-3.5 mt-0.5">
                {timeAgo(w.last_processed_at)}
              </div>
            </button>
          );
        })}
        {wings.length === 0 && (
          <p className="px-3 font-mono text-xs text-slate-fog">
            No wings yet — drop an image into workspace/input/&lt;wing&gt;/
          </p>
        )}
      </nav>
    </aside>
  );
}
