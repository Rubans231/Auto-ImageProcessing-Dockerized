export default function SpecimenHeader({ wing, summary }) {
  if (!summary) return null;
  const drift = summary.latest_analysis?.environmental_drift_detected;
  const hasStamp = drift !== undefined && drift !== null;

  return (
    <div className="contour-bg border-b border-panel-raised px-8 py-6">
      <div className="flex items-start justify-between">
        <h2 className="font-display text-3xl text-parchment">{wing}</h2>
        {hasStamp && (
          <span
            className={`stamp font-mono text-xs uppercase px-3 py-1 ${
              drift ? "text-rust" : "text-moss"
            }`}
          >
            {drift ? "Drift detected" : "Stable"}
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4 mt-5">
        <figure>
          <div className="aspect-video bg-panel rounded-sm overflow-hidden border border-panel-raised">
            {summary.has_baseline ? (
              <img
                src={`/api/wings/${wing}/image/baseline`}
                alt="Baseline reference"
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center font-mono text-xs text-slate-fog">
                no baseline set
              </div>
            )}
          </div>
          <figcaption className="font-mono text-[10px] uppercase tracking-wider text-slate-fog mt-1.5">
            Baseline
          </figcaption>
        </figure>

        <figure>
          <div className="aspect-video bg-panel rounded-sm overflow-hidden border border-panel-raised">
            {summary.has_processed ? (
              <img
                src={`/api/wings/${wing}/image/processed`}
                alt="Latest processed frame"
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center font-mono text-xs text-slate-fog">
                no frames processed yet
              </div>
            )}
          </div>
          <figcaption className="font-mono text-[10px] uppercase tracking-wider text-slate-fog mt-1.5">
            Latest
          </figcaption>
        </figure>
      </div>

      {summary.latest_analysis?.detailed_log && (
        <p className="font-mono text-xs text-slate-fog mt-4 leading-relaxed max-w-2xl">
          {summary.latest_analysis.detailed_log}
        </p>
      )}
    </div>
  );
}
