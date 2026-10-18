import { useEffect, useRef } from "react";

const EXAMPLES = [
  "What hidden risks does Apple carry?",
  "What hidden risks does Novo Nordisk carry?",
  "What breaks if TSMC goes offline for six months?",
  "Find the most dangerous SPOF for Lockheed Martin.",
  "Which companies suffer most from a Suez blackout?",
];

export default function QueryModal({
  open,
  onClose,
  value,
  onChange,
  onSubmit,
  loading,
}: {
  open: boolean;
  onClose: () => void;
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  loading: boolean;
}) {
  const ref = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (open) ref.current?.focus();
  }, [open]);
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-start justify-center pt-32"
      onClick={onClose}
    >
      <div
        className="bg-panel border border-hairline rounded-lg w-full max-w-xl mx-4 shadow-card overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-5 py-4 flex items-center gap-3 border-b border-hairline">
          <span className="mono text-risk text-sm font-semibold">&gt;</span>
          <input
            ref={ref}
            className="flex-1 bg-transparent text-ink text-base mono outline-none placeholder:text-muted"
            placeholder={loading ? "running…" : "scan a company or ask a question"}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && onSubmit()}
            disabled={loading}
          />
          <button
            onClick={onSubmit}
            disabled={loading || !value.trim()}
            className="mono text-[11px] uppercase tracking-wider bg-risk hover:bg-risk/80 disabled:bg-subtle disabled:text-muted text-white px-4 py-1.5 rounded transition"
          >
            {loading ? "…" : "Run"}
          </button>
        </div>
        <div className="px-5 py-3">
          <div className="text-[10px] uppercase tracking-widest text-muted mb-2">
            Examples
          </div>
          <div className="flex flex-col gap-1">
            {EXAMPLES.map((q) => (
              <button
                key={q}
                onClick={() => { onChange(q); setTimeout(onSubmit, 0); }}
                className="text-left text-sm text-inkDim hover:text-ink py-1 flex items-center gap-2 group"
              >
                <span className="text-muted group-hover:text-risk transition">→</span>
                {q}
              </button>
            ))}
          </div>
        </div>
        <div className="px-5 py-2 border-t border-hairline text-[10px] text-muted mono">
          esc to close · ⌘K to reopen
        </div>
      </div>
    </div>
  );
}
