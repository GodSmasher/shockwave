import { WATCHLIST } from "./Watchlist";

export default function DossierLanding({ onSelect }: { onSelect: (query: string) => void }) {
  // Group by sector for feed sections
  const bySector = new Map<string, typeof WATCHLIST>();
  for (const c of WATCHLIST) {
    const list = bySector.get(c.sector) ?? [];
    list.push(c);
    bySector.set(c.sector, list);
  }

  const sectors = Array.from(bySector.entries());

  return (
    <div className="max-w-5xl mx-auto px-6 py-14">
      {/* Masthead */}
      <div className="border-b-2 border-ink pb-6 mb-10">
        <div className="flex items-baseline justify-between flex-wrap gap-4">
          <div className="mono text-[10px] uppercase tracking-[0.25em] text-muted">
            Blindspot Reports · Vol. I · October 2026
          </div>
          <div className="mono text-[10px] uppercase tracking-[0.25em] text-muted">
            17/20 on validation
          </div>
        </div>
      </div>

      {/* Hero manifest */}
      <div className="mb-14">
        <h1 className="display text-6xl md:text-7xl leading-[0.95] text-ink mb-6 tracking-tight">
          Three suppliers Apple's<br />
          CFO has never heard of<br />
          <span className="italic text-inkDim">decide whether iPhones ship.</span>
        </h1>
        <p className="font-sans text-lg leading-[1.75] text-inkDim max-w-2xl first-letter:display first-letter:text-6xl first-letter:float-left first-letter:leading-[0.9] first-letter:mr-3 first-letter:mt-1">
          Shockwave reads a company's supply chain three to four hops upstream.
          Standard Tier-1 risk registers stop at the first ring. What sits in the
          second and third? Of 20 publicly documented single points of failure,
          Shockwave surfaces 17 — most of them below the register's horizon.
        </p>
      </div>

      {/* Sector listings as newspaper columns */}
      <div className="border-t-2 border-ink pt-8">
        <div className="mono text-[10px] uppercase tracking-[0.25em] text-muted mb-6">
          Dossiers in this issue
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-x-10 gap-y-10">
          {sectors.map(([sector, companies]) => (
            <div key={sector}>
              <div className="display italic text-xl text-ink mb-3 pb-2 border-b border-hairline">
                {sector}
              </div>
              <ul className="space-y-3">
                {companies.map((c) => (
                  <li key={c.ticker}>
                    <button
                      onClick={() => onSelect(`What hidden risks does ${c.name} carry?`)}
                      className="group text-left w-full"
                    >
                      <div className="flex items-baseline justify-between gap-2">
                        <span className="display text-xl text-ink group-hover:text-risk transition leading-tight">
                          {c.name}
                        </span>
                        <span className="mono text-[10px] text-muted flex-shrink-0">
                          {c.ticker}
                        </span>
                      </div>
                      <div className="text-[11px] text-muted mt-0.5 font-sans">
                        Read the dossier →
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="mt-20 pt-6 border-t border-hairline text-center text-[11px] mono text-muted">
        FalkorDB · Qwen3-235B · 3-agent reasoning (analyst · skeptic · historian)
      </div>
    </div>
  );
}
