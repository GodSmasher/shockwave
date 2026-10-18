import type { AskResponse, CritiqueResponse, MemoryEntry, PrecedentResponse, Subgraph } from "./types";

const BASE = import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:8000";

export async function ask(question: string): Promise<AskResponse> {
  const r = await fetch(`${BASE}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export type StreamEvent =
  | { type: "start"; question: string }
  | { type: "thinking"; turn: number }
  | { type: "tool_call"; name: string; input: Record<string, any> }
  | { type: "tool_result"; name: string; summary: string }
  | { type: "composing" }
  | { type: "final"; data: AskResponse }
  | { type: "error"; message: string };

export async function askStream(
  question: string,
  onEvent: (ev: StreamEvent) => void
): Promise<AskResponse> {
  const r = await fetch(`${BASE}/ask-stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify({ question }),
  });
  if (!r.ok || !r.body) throw new Error(`HTTP ${r.status}`);
  const reader = r.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let final: AskResponse | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    // SSE events are separated by double newline
    let idx;
    while ((idx = buffer.indexOf("\n\n")) >= 0) {
      const block = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      // Collect data lines
      let dataPayload = "";
      for (const line of block.split("\n")) {
        if (line.startsWith("data: ")) dataPayload += line.slice(6);
      }
      if (!dataPayload) continue;
      try {
        const ev: StreamEvent = JSON.parse(dataPayload);
        onEvent(ev);
        if (ev.type === "final") final = ev.data;
        if (ev.type === "error") throw new Error(ev.message);
      } catch (e) {
        console.warn("stream parse error", dataPayload, e);
      }
    }
  }
  if (!final) throw new Error("stream ended without final event");
  return final;
}

export async function critique(
  analyst_text: string,
  entity_ids: string[],
  question_id: string,
  analysis_id: string,
): Promise<CritiqueResponse> {
  const r = await fetch(`${BASE}/critique`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ analyst_text, entity_ids, question_id, analysis_id }),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function precedent(
  analyst_text: string,
  entity_ids: string[],
  question_id: string,
): Promise<PrecedentResponse> {
  const r = await fetch(`${BASE}/precedent`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ analyst_text, entity_ids, question_id }),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function fetchMemory(limit = 10): Promise<MemoryEntry[]> {
  const r = await fetch(`${BASE}/memory/recent?limit=${limit}`);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function fetchSubgraph(centerId?: string, depth = 2): Promise<Subgraph> {
  const url = new URL(`${BASE}/subgraph`);
  if (centerId) url.searchParams.set("center_id", centerId);
  url.searchParams.set("depth", String(depth));
  url.searchParams.set("limit", "150");
  const r = await fetch(url);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}
