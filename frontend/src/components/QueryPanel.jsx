import { useState } from "react";

export default function QueryPanel({ wing }) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleAsk(e) {
    e.preventDefault();
    if (!question.trim()) return;
    setLoading(true);
    setAnswer("");
    try {
      const res = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ wing, question }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Query failed");
      }
      const data = await res.json();
      setAnswer(data.answer);
    } catch (err) {
      setAnswer(`Couldn't get an answer: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-sm border border-panel-raised bg-panel p-4">
      <h3 className="font-mono text-[11px] uppercase tracking-wider text-slate-fog mb-2">
        Ask the log
      </h3>
      <form onSubmit={handleAsk} className="flex gap-2">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={`What changed recently in ${wing}?`}
          className="flex-1 bg-basalt border border-panel-raised rounded-sm px-3 py-2 text-sm text-parchment placeholder:text-slate-fog focus:outline-none focus:ring-1 focus:ring-moss"
        />
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 rounded-sm bg-moss-dim text-parchment text-sm font-medium hover:bg-moss disabled:opacity-50 transition-colors"
        >
          {loading ? "Asking…" : "Ask"}
        </button>
      </form>
      {answer && (
        <p className="font-mono text-xs text-parchment mt-3 leading-relaxed whitespace-pre-wrap">
          {answer}
        </p>
      )}
    </div>
  );
}
