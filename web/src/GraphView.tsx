import { useEffect, useMemo, useRef, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";
import type { Subgraph } from "./types";

type Props = {
  data: Subgraph;
  highlighted: Set<string>;
  paths: string[][];
  nameToId: Map<string, string>;
};

// Light-theme palette
const typeColor: Record<string, string> = {
  Company: "#2560a8",   // info blue
  Supplier: "#b8762a",  // amber
  Resource: "#7a3b86",  // purple
  Region: "#2f7a60",    // green
  Facility: "#9c4a2e",  // brown
};

export default function GraphView({ data, highlighted, paths, nameToId }: Props) {
  const fgRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dims, setDims] = useState({ w: 760, h: 480 });

  useEffect(() => {
    if (!containerRef.current) return;
    const el = containerRef.current;
    const update = () => {
      setDims({ w: Math.max(300, el.clientWidth), h: Math.max(300, el.clientHeight) });
    };
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const graphData = useMemo(() => {
    const N = data.nodes.length;
    const R = Math.min(dims.w, dims.h) * 0.35;
    const nodes = data.nodes.map((n, i) => {
      const angle = (2 * Math.PI * i) / Math.max(1, N);
      return {
        id: n.id,
        name: n.name,
        type: n.type,
        ticker: n.ticker,
        __highlight: highlighted.has(n.id),
        x: Math.cos(angle) * R + (dims.w / 2),
        y: Math.sin(angle) * R + (dims.h / 2),
      };
    });

    // Highlighted edges = those on paths
    const edgeSet = new Set<string>();
    paths.forEach((p) => {
      for (let i = 0; i < p.length - 1; i++) {
        const a = nameToId.get(p[i]);
        const b = nameToId.get(p[i + 1]);
        if (a && b) {
          edgeSet.add(`${a}->${b}`);
          edgeSet.add(`${b}->${a}`);
        }
      }
    });
    const links = data.edges.map((e) => ({
      source: e.source,
      target: e.target,
      criticality: e.criticality,
      product: e.product,
      __highlight: edgeSet.has(`${e.source}->${e.target}`),
    }));
    return { nodes, links };
  }, [data, highlighted, paths, nameToId, dims.w, dims.h]);

  useEffect(() => {
    if (!fgRef.current) return;
    const fg = fgRef.current;
    try {
      const charge = fg.d3Force("charge");
      if (charge?.strength) charge.strength(-350);
      const link = fg.d3Force("link");
      if (link?.distance) link.distance(80);
      const center = fg.d3Force("center");
      if (center?.strength) center.strength(0.08);
      fg.d3ReheatSimulation();
    } catch {}
    const t = setTimeout(() => fg.zoomToFit?.(700, 50), 1200);
    return () => clearTimeout(t);
  }, [graphData, dims.w, dims.h]);

  return (
    <div ref={containerRef} className="w-full h-full relative">
      <ForceGraph2D
        ref={fgRef as any}
        graphData={graphData}
        width={dims.w}
        height={dims.h}
        cooldownTicks={300}
        d3AlphaDecay={0.012}
        d3VelocityDecay={0.3}
        warmupTicks={100}
        backgroundColor="#faf8f2"
        nodeLabel={(n: any) => `${n.name}${n.ticker ? " (" + n.ticker + ")" : ""} — ${n.type}`}
        linkDirectionalArrowLength={0}
        linkColor={(l: any) => (l.__highlight ? "#b03026" : "rgba(26,26,26,0.18)")}
        linkWidth={(l: any) => (l.__highlight ? 2.5 : 1)}
        nodeCanvasObject={(node: any, ctx, globalScale) => {
          const label = node.name;
          const base = node.__highlight ? 10 : 6;
          const color = typeColor[node.type] || "#777";

          // Outer soft halo for highlighted
          if (node.__highlight) {
            ctx.beginPath();
            ctx.arc(node.x, node.y, base + 6, 0, 2 * Math.PI);
            ctx.fillStyle = color + "22";
            ctx.fill();
          }

          // Node bubble
          ctx.beginPath();
          ctx.arc(node.x, node.y, base, 0, 2 * Math.PI);
          ctx.fillStyle = color;
          ctx.globalAlpha = node.__highlight ? 1 : 0.85;
          ctx.fill();

          // Inner ring on highlighted
          if (node.__highlight) {
            ctx.strokeStyle = "#1a1a1a";
            ctx.lineWidth = 1.5;
            ctx.stroke();
          }
          ctx.globalAlpha = 1;

          // Label
          const showLabel = globalScale > 1.1 || node.__highlight;
          if (showLabel) {
            const fontSize = node.__highlight ? 13 / globalScale : 11 / globalScale;
            ctx.font = `${node.__highlight ? "600" : "400"} ${fontSize}px Inter, sans-serif`;
            const textX = node.x + base + 4;
            const textY = node.y + 3;
            // text background for readability
            const w = ctx.measureText(label).width;
            ctx.fillStyle = "rgba(250,248,242,0.85)";
            ctx.fillRect(textX - 2, textY - fontSize + 1, w + 4, fontSize + 2);
            ctx.fillStyle = node.__highlight ? "#1a1a1a" : "#4a4845";
            ctx.textAlign = "left";
            ctx.fillText(label, textX, textY);
          }
        }}
      />
      <div className="absolute top-3 left-3 bg-panel/90 backdrop-blur rounded px-3 py-1.5 text-[10px] mono uppercase tracking-widest flex gap-4 border border-hairline">
        {Object.entries(typeColor).map(([t, c]) => (
          <div key={t} className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full" style={{ background: c }} />
            <span className="text-muted">{t}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
