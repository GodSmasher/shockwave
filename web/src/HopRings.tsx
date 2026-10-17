import { useMemo } from "react";
import type { Spof } from "./types";

type Node = {
  id: string;
  name: string;
  hop: number;
  angle: number;
  x: number;
  y: number;
  highlighted: boolean;
  tier1: boolean;
};

type Edge = { from: Node; to: Node };

const WIDTH = 760;
const HEIGHT = 480;
const CENTER_X = WIDTH / 2;
const CENTER_Y = HEIGHT / 2;
const RING_RADII = [0, 85, 175, 270];
const COLORS = {
  center: "#b03026",
  highlight: "#b03026",
  tier1: "#2560a8",
  hidden: "#b8762a",
  bg: "transparent",
  ring: "rgba(26,26,26,0.08)",
  edge: "rgba(26,26,26,0.18)",
  edgeHi: "#b03026",
  ink: "#1a1a1a",
  dim: "#8c8880",
};

/** Build nodes placed on concentric rings keyed by min_hops. */
function buildLayout(centerName: string, spofs: Spof[]) {
  const nodes: Node[] = [
    {
      id: "__center__",
      name: centerName,
      hop: 0,
      angle: 0,
      x: CENTER_X,
      y: CENTER_Y,
      highlighted: true,
      tier1: false,
    },
  ];

  // Group by hop
  const byHop = new Map<number, Spof[]>();
  for (const s of spofs) {
    const h = Math.min(3, s.min_hops);
    if (!byHop.has(h)) byHop.set(h, []);
    byHop.get(h)!.push(s);
  }

  // Place on rings
  for (const [hop, items] of byHop) {
    const r = RING_RADII[hop] ?? 300;
    items.sort((a, b) => b.aggregated_impact - a.aggregated_impact);
    const n = items.length;
    items.forEach((s, i) => {
      // Spread evenly on top half if few, full circle if many
      const spread = Math.min(Math.PI * 1.8, Math.PI * 0.5 + n * 0.35);
      const start = -spread / 2;
      const angle = n === 1 ? -Math.PI / 2 : start + (i / Math.max(1, n - 1)) * spread;
      nodes.push({
        id: s.id,
        name: s.name,
        hop,
        angle,
        x: CENTER_X + r * Math.cos(angle - Math.PI / 2),
        y: CENTER_Y + r * Math.sin(angle - Math.PI / 2),
        highlighted: s.min_hops >= 2,
        tier1: s.min_hops === 1,
      });
    });
  }

  // Build edges from sample_paths
  const nameToNode = new Map<string, Node>();
  nodes.forEach((n) => nameToNode.set(n.name, n));
  const edges: Edge[] = [];
  const seen = new Set<string>();
  for (const s of spofs) {
    const path = s.sample_paths[0] || [];
    for (let i = 0; i < path.length - 1; i++) {
      const from = nameToNode.get(path[i]);
      const to = nameToNode.get(path[i + 1]);
      if (!from || !to) continue;
      const k = `${from.id}->${to.id}`;
      if (seen.has(k)) continue;
      seen.add(k);
      edges.push({ from, to });
    }
  }

  return { nodes, edges };
}

export default function HopRings({ centerName, spofs }: { centerName: string; spofs: Spof[] }) {
  const { nodes, edges } = useMemo(() => buildLayout(centerName, spofs), [centerName, spofs]);

  return (
    <svg
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      preserveAspectRatio="xMidYMid meet"
      className="w-full h-full"
      style={{ background: COLORS.bg }}
    >
      {/* Hop rings */}
      {RING_RADII.slice(1).map((r, i) => (
        <g key={r}>
          <circle
            cx={CENTER_X}
            cy={CENTER_Y}
            r={r}
            fill="none"
            stroke={COLORS.ring}
            strokeDasharray="2 4"
          />
          <text
            x={CENTER_X}
            y={CENTER_Y - r + 4}
            textAnchor="middle"
            fontSize="9"
            fill={COLORS.dim}
            fontFamily="JetBrains Mono, monospace"
            style={{ letterSpacing: "0.1em" }}
          >
            {i + 1} HOP
          </text>
        </g>
      ))}

      {/* Edges */}
      {edges.map((e, i) => {
        const highlighted = e.from.highlighted || e.to.highlighted;
        return (
          <line
            key={i}
            x1={e.from.x}
            y1={e.from.y}
            x2={e.to.x}
            y2={e.to.y}
            stroke={highlighted ? COLORS.edgeHi : COLORS.edge}
            strokeWidth={highlighted ? 1.5 : 1}
            strokeOpacity={highlighted ? 0.6 : 0.4}
          />
        );
      })}

      {/* Nodes + labels */}
      {nodes.map((n) => {
        const isCenter = n.hop === 0;
        const r = isCenter ? 10 : n.highlighted ? 6 : 5;
        const color = isCenter
          ? COLORS.center
          : n.tier1
          ? COLORS.tier1
          : COLORS.hidden;

        // Label position outside the ring
        const labelAngle = n.angle - Math.PI / 2;
        const labelR = isCenter ? 0 : (RING_RADII[n.hop] ?? 0) + 18;
        const labelX = isCenter ? n.x : CENTER_X + labelR * Math.cos(labelAngle);
        const labelY = isCenter ? n.y + 24 : CENTER_Y + labelR * Math.sin(labelAngle);
        const anchor =
          Math.abs(labelX - CENTER_X) < 20
            ? "middle"
            : labelX > CENTER_X
            ? "start"
            : "end";

        return (
          <g key={n.id}>
            <circle
              cx={n.x}
              cy={n.y}
              r={r}
              fill={color}
              stroke={isCenter ? "#fff" : "none"}
              strokeWidth={isCenter ? 1 : 0}
              opacity={isCenter ? 1 : n.highlighted ? 1 : 0.85}
            />
            {n.highlighted && !isCenter && (
              <circle cx={n.x} cy={n.y} r={r + 3} fill="none" stroke={color} strokeOpacity={0.3} />
            )}
            <text
              x={labelX}
              y={labelY}
              textAnchor={anchor as any}
              fontSize={isCenter ? "16" : "11"}
              fill={isCenter ? COLORS.ink : n.highlighted ? COLORS.ink : COLORS.dim}
              fontFamily={isCenter ? "Instrument Serif, Georgia, serif" : "Inter, sans-serif"}
              fontStyle={isCenter ? "normal" : "normal"}
            >
              {n.name}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
