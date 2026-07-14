export default function StatusBar({ status, health }) {
  const rooms = status?.by_room ? Object.entries(status.by_room) : [];
  return (
    <div className="border-t border-panel-raised bg-panel px-8 py-2 flex items-center gap-4 font-mono text-[10px] text-slate-fog">
      <span className={health?.palace_dir_exists ? "text-moss" : "text-rust"}>
        ● palace {health?.palace_dir_exists ? "online" : "unreachable"}
      </span>
      {rooms.length > 0 && (
        <span className="text-panel-raised">|</span>
      )}
      {rooms.map(([room, count]) => (
        <span key={room}>
          {room}: {count} filed
        </span>
      ))}
    </div>
  );
}
