import { useState } from "react";
import { WATCHLIST } from "./Watchlist";

export default function TopNav({
  onSelect,
  active,
  onQuery,
}: {
  onSelect: (query: string) => void;
  active?: string;
  onQuery: () => void;
}) {
  const [open, setOpen] = useState(false);

  return (
    <header className="relative border-b border-hairline bg-bg/95 backdrop-blur z-20">
      <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-baseline gap-3">
          <a href="/" className="display text-2xl text-ink tracking-tight">
            Shockwave
          </a>
          <span className="mono text-[10px] uppercase tracking-widest text-muted">
            Blindspot Reports
          </span>
        </div>

        {active && (
          <div className="hidden md:block">
            <span className="mono text-[10px] uppercase tracking-widest text-muted">
              now reading ·
            </span>{" "}
            <span className="display italic text-base text-inkDim">{active}</span>
          </div>
        )}

        <div className="flex items-center gap-4 text-[11px] mono text-inkDim">
          <button
            onClick={() => setOpen((o) => !o)}
            className="border border-hairline hover:border-ink rounded px-2 py-1 transition"
          >
            Browse ↓
          </button>
          <button
            onClick={onQuery}
            className="border border-hairline hover:border-risk rounded px-2 py-1 transition"
            title="⌘K"
          >
            Ask
          </button>
        </div>
      </div>

      {open && (
        <div className="absolute top-full left-0 right-0 bg-bg border-b border-hairline shadow-card">
          <div className="max-w-6xl mx-auto px-6 py-5">
            <div className="text-[10px] uppercase tracking-widest text-muted mb-3">
              Dossiers
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-x-6 gap-y-1">
              {WATCHLIST.map((c) => (
                <button
                  key={c.ticker}
                  onClick={() => {
                    setOpen(false);
                    onSelect(`Welche versteckten Risiken hat ${c.name}?`);
                  }}
                  className="text-left py-2 border-b border-hairline/60 flex items-baseline justify-between group hover:bg-panelHi/60 px-1 transition"
                >
                  <span className="display text-base text-ink group-hover:text-risk">
                    {c.name}
                  </span>
                  <span className="mono text-[10px] text-muted">{c.ticker}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
