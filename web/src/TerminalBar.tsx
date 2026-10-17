import { useRef } from "react";

type Props = {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  loading: boolean;
};

const EXAMPLES = [
  "Welche versteckten Risiken hat Apple?",
  "Was passiert wenn TSMC 6 Monate ausfällt?",
  "Finde den gefährlichsten SPOF für Nvidia.",
  "Welche Firmen leiden am meisten unter einem Suez-Blackout?",
];

export default function TerminalBar({ value, onChange, onSubmit, loading }: Props) {
  const ref = useRef<HTMLInputElement>(null);

  return (
    <div className="border-t border-hairline bg-panel">
      <div className="px-4 py-1.5 border-b border-hairline/50 flex gap-2 overflow-x-auto">
        <span className="text-[10px] uppercase tracking-wider text-muted font-semibold flex-shrink-0 self-center">
          Examples
        </span>
        {EXAMPLES.map((q) => (
          <button
            key={q}
            onClick={() => { onChange(q); setTimeout(onSubmit, 0); }}
            className="text-[11px] text-inkDim hover:text-ink border border-hairline hover:border-risk/50 rounded px-2 py-0.5 whitespace-nowrap transition"
          >
            {q}
          </button>
        ))}
      </div>
      <div className="px-4 py-3 flex items-center gap-3">
        <span className="mono text-risk text-sm font-semibold select-none">&gt;</span>
        <input
          ref={ref}
          className="flex-1 bg-transparent text-ink text-sm mono outline-none placeholder:text-muted"
          placeholder={loading ? "running analysis..." : "scan [company] [query]"}
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
    </div>
  );
}
