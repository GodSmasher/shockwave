import { useMemo } from "react";
import GraphView from "./GraphView";
import type { AskResponse, CritiqueResponse, PrecedentResponse, Spof, Subgraph } from "./types";

type Props = {
  result: AskResponse;
  skeptic: CritiqueResponse | null;
  historian: PrecedentResponse | null;
  subgraph: Subgraph;
  nameToId: Map<string, string>;
};

function dateString(): string {
  return new Date().toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function firstParagraph(text: string): string {
  const trimmed = text.trim();
  const bulletIdx = trimmed.search(/\n\s*[-•]/);
  if (bulletIdx > 0) return trimmed.slice(0, bulletIdx).trim();
  const twoLineIdx = trimmed.indexOf("\n\n");
  if (twoLineIdx > 0) return trimmed.slice(0, twoLineIdx).trim();
  return trimmed;
}

function restOfBody(text: string): string {
  const lede = firstParagraph(text);
  return text.replace(lede, "").trim();
}

function Section({ eyebrow, title, children }: { eyebrow: string; title: string; children: React.ReactNode }) {
  return (
    <section className="mt-14">
      <div className="mono text-[10px] uppercase tracking-[0.25em] text-muted mb-2">
        {eyebrow}
      </div>
      <h2 className="display text-3xl text-ink mb-5 leading-tight">
        {title}
      </h2>
      {children}
    </section>
  );
}

function PathPill({ path }: { path: string[] }) {
  return (
    <div className="inline-flex items-center gap-1 flex-wrap text-[11px] mono bg-panelHi/80 rounded px-2 py-1 border border-hairline">
      {path.map((n, i) => (
        <span key={i} className="flex items-center gap-1">
          <span className={i === path.length - 1 ? "text-risk" : "text-inkDim"}>{n}</span>
          {i < path.length - 1 && <span className="text-muted">→</span>}
        </span>
      ))}
    </div>
  );
}

function HiddenSpofCard({ s }: { s: Spof }) {
  return (
    <div className="py-5 border-b border-hairline last:border-b-0">
      <div className="flex items-baseline justify-between gap-4 mb-2">
        <div>
          <div className="display text-2xl text-ink leading-tight">{s.name}</div>
          <div className="text-[11px] text-muted mt-0.5">
            {s.type} · {s.min_hops} hops upstream
          </div>
        </div>
        <div className="text-right flex-shrink-0">
          <div className="mono text-xs text-muted uppercase tracking-wider">impact</div>
          <div className="display text-2xl text-risk">{s.aggregated_impact.toFixed(2)}</div>
        </div>
      </div>
      {s.sample_paths[0] && (
        <div className="mt-3">
          <PathPill path={s.sample_paths[0]} />
        </div>
      )}
    </div>
  );
}

function Pending({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-2 text-[11px] mono text-muted uppercase tracking-wider py-3">
      <span className="w-1.5 h-1.5 rounded-full bg-warn animate-pulse" />
      {label}
    </div>
  );
}

export default function Dossier({ result, skeptic, historian, subgraph, nameToId }: Props) {
  const centerName = result.center_entity?.name || "Unknown";
  const spofs = result.blindspot ?? [];
  const tier1 = spofs.filter((s) => s.min_hops === 1);
  const hidden = spofs.filter((s) => s.min_hops >= 2);
  const analystLede = firstParagraph(result.answer);
  const analystBody = restOfBody(result.answer);
  const hiddenCount = hidden.length;
  const highlighted = useMemo(() => new Set(result.highlighted_ids), [result]);

  // Focused subgraph: only highlighted nodes + their immediate neighbors on paths
  const focusGraph = useMemo(() => {
    const relevant = new Set<string>(result.highlighted_ids);
    if (result.center_entity) relevant.add(result.center_entity.id);
    for (const p of result.paths) {
      for (const name of p) {
        const id = nameToId.get(name);
        if (id) relevant.add(id);
      }
    }
    const nodes = subgraph.nodes.filter((n) => relevant.has(n.id));
    const nodeIds = new Set(nodes.map((n) => n.id));
    const edges = subgraph.edges.filter(
      (e) => nodeIds.has(e.source) && nodeIds.has(e.target)
    );
    return { nodes, edges };
  }, [subgraph, result, nameToId]);

  return (
    <article className="max-w-3xl mx-auto px-6 py-12">
      {/* Eyebrow */}
      <div className="mono text-[10px] uppercase tracking-[0.25em] text-muted mb-4">
        Blindspot Report · {dateString()}
      </div>

      {/* Headline */}
      <h1 className="display text-5xl md:text-6xl leading-[1.0] text-ink mb-4 tracking-tight">
        {centerName}
      </h1>

      {/* Deck */}
      <p className="display italic text-2xl text-inkDim leading-snug mb-6 max-w-2xl">
        {hiddenCount > 0
          ? `${hiddenCount} ${hiddenCount === 1 ? "supplier" : "suppliers"} your Tier-1 risk register will never surface.`
          : `No hidden single points of failure found in the current graph.`}
      </p>

      {/* Byline */}
      <div className="flex items-baseline gap-3 text-[11px] mono text-muted mb-10 pb-8 border-b border-hairline">
        <span>By <span className="text-ink">Shockwave</span></span>
        <span>·</span>
        <span>{result.turns} turns</span>
        <span>·</span>
        <span>{result.trace.length} tool calls</span>
      </div>

      {/* Lede */}
      <p className="font-sans text-lg leading-[1.7] text-ink mb-10 first-letter:display first-letter:text-6xl first-letter:float-left first-letter:leading-[1] first-letter:mr-3 first-letter:mt-1">
        {analystLede || `Shockwave traced ${centerName}'s dependency topology up to four hops upstream.`}
      </p>

      {/* Hero fact */}
      {hiddenCount > 0 && (
        <div className="my-14 py-10 border-y-2 border-risk/40 text-center">
          <div className="display text-7xl text-risk leading-none mb-3">
            {hiddenCount}
          </div>
          <div className="display italic text-xl text-inkDim">
            hidden suppliers {centerName}'s risk register doesn't surface.
          </div>
        </div>
      )}

      {/* THE HIDDEN */}
      {hidden.length > 0 && (
        <Section
          eyebrow="Section I"
          title={hidden.length === 1 ? "The hidden one." : hidden.length === 3 ? "The hidden three." : `The hidden ${hidden.length}.`}
        >
          <div className="mt-6">
            {hidden.slice(0, 5).map((s) => (
              <HiddenSpofCard key={s.id} s={s} />
            ))}
          </div>
          {tier1.length > 0 && (
            <div className="mt-8 pt-6 border-t border-hairline">
              <div className="text-[11px] text-muted mono uppercase tracking-wider mb-3">
                Already in the register — direct tier-1
              </div>
              <div className="flex flex-wrap gap-2">
                {tier1.map((t) => (
                  <div key={t.id} className="text-[11px] mono bg-panelHi border border-hairline rounded px-2 py-1 text-inkDim">
                    {t.name} · {t.aggregated_impact.toFixed(2)}
                  </div>
                ))}
              </div>
            </div>
          )}
        </Section>
      )}

      {/* Analyst body */}
      {analystBody && (
        <Section eyebrow="Analyst report" title="What the chain says.">
          <div className="font-sans text-base leading-[1.75] text-ink whitespace-pre-wrap">
            {analystBody}
          </div>
        </Section>
      )}

      {/* Figure 1 — Force-directed bubbles */}
      <Section eyebrow="Figure 1" title="The dependency chain.">
        <div className="h-[520px] rounded-lg border border-hairline bg-panel overflow-hidden shadow-card">
          <GraphView
            data={focusGraph}
            highlighted={highlighted}
            paths={result.paths}
            nameToId={nameToId}
          />
        </div>
        <div className="mt-3 text-[11px] text-muted font-sans italic">
          {focusGraph.nodes.length} nodes · {focusGraph.edges.length} dependencies ·
          red edges follow the propagation path. Drag to rearrange.
        </div>
      </Section>

      {/* Historian */}
      <Section eyebrow="Section II" title="What history teaches.">
        {!historian ? (
          <Pending label="Historian is reading precedent …" />
        ) : (
          <div className="fade-in">
            <div className="font-sans text-base leading-[1.75] text-ink whitespace-pre-wrap">
              {historian.historian}
            </div>
            {historian.historian_trace.length > 0 && (
              <div className="mt-4 text-[10px] text-muted mono">
                Sourced: {historian.historian_trace.map((t) => t.tool).join(" · ")}
              </div>
            )}
          </div>
        )}
      </Section>

      {/* Skeptic */}
      <Section eyebrow="Section III" title="Counterpoint.">
        {!skeptic ? (
          <Pending label="Skeptic is drafting objections …" />
        ) : (
          <div className="fade-in">
            <div className="font-sans text-base leading-[1.75] text-ink whitespace-pre-wrap">
              {skeptic.skeptic}
            </div>
            {skeptic.skeptic_trace.length > 0 && (
              <div className="mt-4 text-[10px] text-muted mono">
                Sourced: {skeptic.skeptic_trace.map((t) => t.tool).join(" · ")}
              </div>
            )}
          </div>
        )}
      </Section>

      {/* Colophon */}
      <div className="mt-20 pt-6 border-t border-hairline text-center text-[11px] mono text-muted">
        <div>FalkorDB · Qwen3-235B · analyst · skeptic · historian</div>
        <div className="mt-1">17/20 on validation — 85% recall on documented SPOFs</div>
      </div>
    </article>
  );
}
