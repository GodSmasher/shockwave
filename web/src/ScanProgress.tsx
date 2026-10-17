import { useEffect, useRef } from "react";

export type ProgressStep = {
  id: string;
  label: string;
  done: boolean;
  detail?: string;
  tsMs: number;
};

const TOOL_LABEL: Record<string, string> = {
  find_entity: "Searching the graph",
  simulate_shock: "Running cascade simulation",
  find_hidden_spofs: "Tracing hidden single points of failure",
};

export default function ScanProgress({
  steps,
  question,
  elapsedMs,
}: {
  steps: ProgressStep[];
  question: string;
  elapsedMs: number;
}) {
  const bottomRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [steps.length]);

  const secs = (elapsedMs / 1000).toFixed(1);

  return (
    <div className="max-w-2xl mx-auto px-6 py-16">
      <div className="mono text-[10px] uppercase tracking-[0.25em] text-muted mb-4">
        Scanning · {secs}s elapsed
      </div>
      <h2 className="display text-3xl text-ink leading-snug mb-8">
        {question}
      </h2>

      <div className="border-l-2 border-hairline pl-5 space-y-4">
        {steps.map((s) => (
          <div key={s.id} className="relative">
            <div
              className={`absolute -left-[26px] top-1 w-2 h-2 rounded-full border-2 border-bg ${
                s.done ? "bg-ok" : "bg-warn animate-pulse"
              }`}
            />
            <div className="flex items-baseline justify-between gap-3">
              <div className="mono text-[11px] uppercase tracking-wider text-inkDim">
                {s.label}
              </div>
              <div className="mono text-[10px] text-muted flex-shrink-0">
                {(s.tsMs / 1000).toFixed(1)}s
              </div>
            </div>
            {s.detail && (
              <div className="font-sans text-sm text-ink mt-0.5">
                {s.detail}
              </div>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="mt-10 text-[11px] mono text-muted">
        Three agents are reading the graph · analyst → skeptic → historian
      </div>
    </div>
  );
}

export { TOOL_LABEL };
