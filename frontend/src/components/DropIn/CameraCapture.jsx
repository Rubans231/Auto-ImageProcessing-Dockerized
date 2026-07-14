import { useRef, useState, useEffect, useCallback } from "react";
import { api } from "../../api.js";

export default function CameraCapture({ wing, room, defaultInterval }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const timerRef = useRef(null);

  const [active, setActive] = useState(false);
  const [intervalSeconds, setIntervalSeconds] = useState(defaultInterval || 10);
  const [lastCaptureAt, setLastCaptureAt] = useState(null);
  const [captureCount, setCaptureCount] = useState(0);
  const [error, setError] = useState("");

  const captureFrame = useCallback(async () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || !video.videoWidth) return;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);

    canvas.toBlob(
      async (blob) => {
        if (!blob) return;
        const form = new FormData();
        form.append("files", blob, `cam_${Date.now()}.jpg`);
        const params = room ? `?room=${encodeURIComponent(room)}` : "";
        try {
          await api.upload(`/wings/${wing}/upload${params}`, form);
          setLastCaptureAt(new Date());
          setCaptureCount((c) => c + 1);
        } catch (err) {
          setError(err.message);
        }
      },
      "image/jpeg",
      0.9
    );
  }, [wing, room]);

  async function start() {
    setError("");
    if (!window.isSecureContext) {
      setError(
        "Camera access needs a secure context (localhost or HTTPS) — the browser blocks it otherwise."
      );
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setActive(true);
    } catch (err) {
      setError(`Couldn't access camera: ${err.message}`);
    }
  }

  function stop() {
    setActive(false);
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
  }

  useEffect(() => {
    if (active) {
      timerRef.current = setInterval(captureFrame, Math.max(intervalSeconds, 1) * 1000);
      return () => clearInterval(timerRef.current);
    }
  }, [active, intervalSeconds, captureFrame]);

  useEffect(() => () => stop(), []); // release the camera if the component unmounts mid-capture

  return (
    <div className="grid grid-cols-2 gap-4">
      <div>
        <video
          ref={videoRef}
          muted
          playsInline
          className="w-full aspect-video bg-basalt rounded-sm border border-panel-raised object-cover"
        />
        <canvas ref={canvasRef} className="hidden" />
      </div>
      <div className="space-y-3">
        <div>
          <label className="font-mono text-[11px] uppercase tracking-wider text-slate-fog block mb-1">
            Capture interval (seconds)
          </label>
          <input
            type="number"
            min="1"
            value={intervalSeconds}
            onChange={(e) => setIntervalSeconds(Number(e.target.value))}
            className="w-32 bg-basalt border border-panel-raised rounded-sm px-3 py-1.5 text-sm text-parchment"
          />
        </div>
        <button
          onClick={active ? stop : start}
          className={`px-4 py-2 text-sm rounded-sm transition-colors ${
            active
              ? "bg-rust-dim text-parchment hover:bg-rust"
              : "bg-moss-dim text-parchment hover:bg-moss"
          }`}
        >
          {active ? "Stop capture" : "Start capture"}
        </button>
        {active && (
          <p className="font-mono text-[11px] text-slate-fog">
            {captureCount} frame{captureCount === 1 ? "" : "s"} sent
            {lastCaptureAt ? ` · last at ${lastCaptureAt.toLocaleTimeString()}` : ""}
          </p>
        )}
        {error && <p className="font-mono text-xs text-rust">{error}</p>}
        <p className="font-mono text-[10px] text-slate-fog">
          This captures from whatever camera the browser has access to on this
          device. For a camera on a different machine, use the "connect a
          cam" script (cam_capture.py) instead — see the Deployment guide.
        </p>
      </div>
    </div>
  );
}
