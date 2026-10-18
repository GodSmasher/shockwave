import type { Spof } from "./types";

function ImpactBar({ value, highlight }: { value: number; highlight?: boolean }) {
  const pct = Math.min(100, Math.round(value * 100));
  return (
    <div className="w-full h-1.5 bg-subtle rounded overflow-hidden">
      <div
        className={`h-full ${highlight ? "bg-accent" : "bg-accent2"}`}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

function PathChain({ path }: { path: string[] }) {
  return (
    <div className="flex items-center gap-1 flex-wrap text-[11px]">
      {path.map((name, i) => (
        <span key={i} className="flex items-center gap-1">
          <span className={i === path.length - 1 ? "text-accent font-medium" : "text-muted"}>
            {name}
          </span>
          {i < path.length - 1 && <span className="text-muted/50">→</span>}
        </span>
      ))}
    </div>
  );
}

export default function BlindspotReport({
  spofs,
  centerName,
}: {
  spofs: Spof[];
  centerName: string;
}) {
  if (!spofs || spofs.length === 0) return null;

  const tier1 = spofs.filter((s) => s.min_hops === 1).sort((a, b) => b.aggregated_impact - a.aggregated_impact);
  const hidden = spofs.filter((s) => s.min_hops >= 2).sort((a, b) => b.hidden_score - a.hidden_score);

  return (
    <div className="mt-4 border border-subtle rounded-lg overflow-hidden">
      <div className="bg-panel px-4 py-2 border-b border-subtle text-xs uppercase tracking-wider text-muted font-medium">
        Blindspot Report · {centerName}
      </div>
      <div className="grid grid-cols-2 divide-x divide-subtle">
        {/* Left: Classic risk register */}
        <div className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-2 h-2 rounded-full bg-accent2" />
            <span className="text-xs font-medium text-accent2 uppercase tracking-wider">
              Risk Register
            </span>
            <span className="text-[10px] text-muted">(Tier-1, bekannt)</span>
          </div>
          <div className="space-y-2.5">
            {tier1.length === 0 && (
              <div className="text-xs text-muted">No tier-1 risks in the graph.</div>
            )}
            {tier1.map((s) => (
              <div key={s.id} className="space-y-1">
                <div className="flex items-center justify-between gap-2">
                  <div className="text-sm font-medium truncate">{s.name}</div>
                  <div className="text-[10px] text-muted font-mono flex-shrink-0">
                    {s.aggregated_impact.toFixed(2)}
                  </div>
                </div>
                <ImpactBar value={s.aggregated_impact} />
                <div className="text-[10px] text-muted">{s.type}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Shockwave's hidden find */}
        <div className="p-4 bg-accent/5">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-2 h-2 rounded-full bg-accent animate-pulse" />
            <span className="text-xs font-medium text-accent uppercase tracking-wider">
              Shockwave findet
            </span>
            <span className="text-[10px] text-muted">(2–3 Hops entfernt)</span>
          </div>
          <div className="space-y-3">
            {hidden.length === 0 && (
              <div className="text-xs text-muted italic">
                No hidden SPOFs found.
              </div>
            )}
            {hidden.map((s) => (
              <div key={s.id} className="space-y-1.5">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <div className="text-sm font-semibold truncate">{s.name}</div>
                    <span className="text-[9px] bg-accent text-white px-1.5 py-0.5 rounded font-mono flex-shrink-0">
                      {s.min_hops} HOPS
                    </span>
                  </div>
                  <div className="text-[10px] text-muted font-mono flex-shrink-0">
                    {s.aggregated_impact.toFixed(2)}
                  </div>
                </div>
                <ImpactBar value={s.aggregated_impact} highlight />
                {s.sample_paths[0] && <PathChain path={s.sample_paths[0]} />}
              </div>
            ))}
          </div>
        </div>
      </div>
      {hidden.length > 0 && (
        <div className="bg-accent/10 px-4 py-2 text-[11px] text-accent border-t border-accent/20">
          ↑ These {hidden.length} risks appear in no standard Tier-1 register —
          they sit {hidden[0].min_hops}+ supply-chain hops away.
        </div>
      )}
    </div>
  );
}
