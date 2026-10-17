import { useEffect, useMemo, useState } from "react";
import { askStream, critique, fetchSubgraph, precedent } from "./api";
import type { StreamEvent } from "./api";
import Dossier from "./Dossier";
import DossierLanding from "./DossierLanding";
import TopNav from "./TopNav";
import QueryModal from "./QueryModal";
import ScanProgress, { TOOL_LABEL, type ProgressStep } from "./ScanProgress";
import type { AskResponse, CritiqueResponse, PrecedentResponse, Subgraph } from "./types";

export default function App() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AskResponse | null>(null);
  const [sk, setSk] = useState<CritiqueResponse | null>(null);
  const [hi, setHi] = useState<PrecedentResponse | null>(null);
  const [subgraph, setSubgraph] = useState<Subgraph>({ nodes: [], edges: [] });
  const [error, setError] = useState<string | null>(null);
  const [queryOpen, setQueryOpen] = useState(false);
  const [steps, setSteps] = useState<ProgressStep[]>([]);
  const [scanQuestion, setScanQuestion] = useState("");
  const [startedAt, setStartedAt] = useState(0);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    fetchSubgraph().then(setSubgraph).catch(() => {});
  }, []);

  // Tick elapsed timer during loading
  useEffect(() => {
    if (!loading) return;
    const id = setInterval(() => setTick((t) => t + 1), 100);
    return () => clearInterval(id);
  }, [loading]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setQueryOpen(true);
      }
      if (e.key === "/" && !queryOpen) {
        const el = document.activeElement as HTMLElement | null;
        if (!el || !["INPUT", "TEXTAREA"].includes(el.tagName)) {
          e.preventDefault();
          setQueryOpen(true);
        }
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [queryOpen]);

  const nameToId = useMemo(() => {
    const m = new Map<string, string>();
    for (const n of subgraph.nodes) m.set(n.name, n.id);
    return m;
  }, [subgraph]);

  async function submit(q?: string) {
    const query = (q ?? question).trim();
    if (!query || loading) return;
    setLoading(true);
    setError(null);
    setQueryOpen(false);
    setResult(null);
    setSk(null);
    setHi(null);
    setSteps([]);
    setScanQuestion(query);
    const t0 = Date.now();
    setStartedAt(t0);

    const addStep = (step: Omit<ProgressStep, "tsMs">) => {
      const tsMs = Date.now() - t0;
      setSteps((prev) => {
        // dedupe if same id — mark done + merge detail
        const existing = prev.find((p) => p.id === step.id);
        if (existing) {
          return prev.map((p) =>
            p.id === step.id ? { ...p, ...step, tsMs } : p
          );
        }
        return [...prev, { ...step, tsMs }];
      });
    };

    try {
      const r = await askStream(query, (ev: StreamEvent) => {
        switch (ev.type) {
          case "start":
            addStep({ id: "start", label: "Reading your question", done: true });
            break;
          case "thinking": {
            addStep({
              id: `think_${ev.turn}`,
              label: ev.turn === 1 ? "Analyst deciding where to look" : "Analyst reasoning",
              done: false,
            });
            break;
          }
          case "tool_call": {
            // Mark previous thinking step done
            setSteps((prev) =>
              prev.map((p) =>
                p.id.startsWith("think_") && !p.done ? { ...p, done: true } : p
              )
            );
            const label = TOOL_LABEL[ev.name] || ev.name;
            const detail = ev.input?.query || ev.input?.target_id || "";
            addStep({ id: `t_${ev.name}_${Math.random()}`, label, done: false, detail });
            break;
          }
          case "tool_result": {
            // mark most recent tool step done with summary
            setSteps((prev) => {
              const copy = [...prev];
              for (let i = copy.length - 1; i >= 0; i--) {
                if (copy[i].id.startsWith("t_") && !copy[i].done) {
                  copy[i] = { ...copy[i], done: true, detail: ev.summary };
                  break;
                }
              }
              return copy;
            });
            break;
          }
          case "composing":
            setSteps((prev) =>
              prev.map((p) =>
                p.id.startsWith("think_") && !p.done ? { ...p, done: true } : p
              )
            );
            addStep({ id: "composing", label: "Analyst composing the dossier", done: false });
            break;
          case "final":
            setSteps((prev) =>
              prev.map((p) => (!p.done ? { ...p, done: true } : p))
            );
            addStep({ id: "done", label: "Dossier ready", done: true });
            break;
        }
      });

      setResult(r);
      setLoading(false);
      setQuestion("");
      window.scrollTo({ top: 0, behavior: "smooth" });

      critique(r.answer, r.highlighted_ids, r.question_id, r.analysis_id)
        .then(setSk)
        .catch((e) => setSk({ skeptic: `[Skeptic Fehler: ${e.message || e}]`, skeptic_trace: [] }));
      precedent(r.answer, r.highlighted_ids, r.question_id)
        .then(setHi)
        .catch((e) => setHi({ historian: `[Historian Fehler: ${e.message || e}]`, historian_trace: [] }));
    } catch (e: any) {
      setError(e.message || String(e));
      setLoading(false);
    }
  }

  const centerName = result?.center_entity?.name;
  const elapsedMs = loading ? Date.now() - startedAt + tick - tick : loading ? 0 : 0;
  // explicit dependency on tick to force re-render each tick
  const liveElapsed = loading ? (tick, Date.now() - startedAt) : 0;

  return (
    <div className="min-h-full flex flex-col">
      <TopNav
        onSelect={submit}
        active={centerName}
        onQuery={() => setQueryOpen(true)}
      />

      <main className="flex-1">
        {error && (
          <div className="max-w-3xl mx-auto mt-6 px-6">
            <div className="bg-risk/10 border border-risk rounded p-3 text-sm">{error}</div>
          </div>
        )}

        {loading && (
          <ScanProgress steps={steps} question={scanQuestion} elapsedMs={liveElapsed} />
        )}

        {!loading && result && (
          <Dossier result={result} skeptic={sk} historian={hi} subgraph={subgraph} nameToId={nameToId} />
        )}

        {!loading && !result && (
          <DossierLanding onSelect={submit} />
        )}
      </main>

      <QueryModal
        open={queryOpen}
        onClose={() => setQueryOpen(false)}
        value={question}
        onChange={setQuestion}
        onSubmit={() => submit()}
        loading={loading}
      />
    </div>
  );
}
