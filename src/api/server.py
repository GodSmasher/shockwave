"""FastAPI backend for Shockwave UI.

Endpoints:
  POST /ask       — run the analyst agent, return trace + final text
  GET  /subgraph  — fetch nodes+edges around a center node (for visualization)
  GET  /entity    — fuzzy entity lookup (chat typeahead)
"""
import json
import os
import queue
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.agent.analyst import analyze
from src.agent.skeptic import challenge
from src.agent.historian import contextualize
from src.graph.entity import find_entity
from src.graph.connection import get_graph
from src.graph.memory import recent_analyses

app = FastAPI(title="Shockwave API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskReq(BaseModel):
    question: str


def _extract_structured(result_trace: list[dict]) -> dict:
    highlighted: set[str] = set()
    paths: list[list[str]] = []
    blindspot_data: list[dict] | None = None
    cascade_data: list[dict] | None = None
    center_entity: dict | None = None

    for t in result_trace:
        name = t["tool"]
        out = t.get("output_full")
        if not isinstance(out, (list, dict)):
            continue
        if name == "find_entity" and isinstance(out, list) and out and center_entity is None:
            center_entity = out[0]
        if name == "find_hidden_spofs" and isinstance(out, list):
            blindspot_data = out
            for item in out:
                if "id" in item:
                    highlighted.add(item["id"])
                for p in item.get("sample_paths", []):
                    if isinstance(p, list):
                        paths.append(p)
        if name == "simulate_shock" and isinstance(out, list):
            cascade_data = out
            for item in out:
                if "company_id" in item:
                    highlighted.add(item["company_id"])
                if isinstance(item.get("chain"), list):
                    paths.append(item["chain"])
    return {
        "highlighted_ids": sorted(highlighted),
        "paths": paths,
        "blindspot": blindspot_data,
        "cascade": cascade_data,
        "center_entity": center_entity,
    }


@app.post("/ask")
def ask(req: AskReq):
    """Fast endpoint: returns Analyst only. UI polls /critique + /precedent next."""
    result = analyze(req.question, trace=False)
    structured = _extract_structured(result["trace"])
    return {
        "question": req.question,
        "answer": result["final_text"],
        "trace": [{"tool": t["tool"], "input": t["input"]} for t in result["trace"]],
        "turns": result["turns"],
        "question_id": result.get("question_id", ""),
        "analysis_id": result.get("analysis_id", ""),
        "analyst_text": result["final_text"],
        **structured,
    }


@app.post("/ask-stream")
async def ask_stream(req: AskReq):
    """Streaming endpoint — yields NDJSON events while the analyst runs."""
    import asyncio
    loop = asyncio.get_running_loop()
    aq: asyncio.Queue = asyncio.Queue()

    def on_event(ev: dict):
        # Called from worker thread; schedule put on event loop
        loop.call_soon_threadsafe(aq.put_nowait, ev)

    def worker():
        try:
            result = analyze(req.question, trace=False, on_event=on_event)
            structured = _extract_structured(result["trace"])
            loop.call_soon_threadsafe(aq.put_nowait, {
                "type": "final",
                "data": {
                    "question": req.question,
                    "answer": result["final_text"],
                    "trace": [{"tool": t["tool"], "input": t["input"]} for t in result["trace"]],
                    "turns": result["turns"],
                    "question_id": result.get("question_id", ""),
                    "analysis_id": result.get("analysis_id", ""),
                    **structured,
                },
            })
        except Exception as e:
            loop.call_soon_threadsafe(aq.put_nowait, {"type": "error", "message": str(e)})
        finally:
            loop.call_soon_threadsafe(aq.put_nowait, None)

    threading.Thread(target=worker, daemon=True).start()

    async def gen():
        while True:
            item = await aq.get()
            if item is None:
                break
            # SSE format: "data: <json>\n\n"
            yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


class CritiqueReq(BaseModel):
    analyst_text: str
    entity_ids: list[str]
    question_id: str = ""
    analysis_id: str = ""


@app.post("/critique")
def critique(req: CritiqueReq):
    try:
        sk = challenge(req.analyst_text, req.entity_ids, req.question_id, req.analysis_id)
        return {
            "skeptic": sk["text"],
            "skeptic_trace": [{"tool": t["tool"], "input": t["input"]} for t in sk.get("trace", [])],
        }
    except Exception as e:
        return {"skeptic": f"[Skeptic Fehler: {e}]", "skeptic_trace": []}


class PrecedentReq(BaseModel):
    analyst_text: str
    entity_ids: list[str]
    question_id: str = ""


@app.post("/precedent")
def precedent(req: PrecedentReq):
    try:
        hi = contextualize(req.analyst_text, req.entity_ids, req.question_id)
        return {
            "historian": hi["text"],
            "historian_trace": [{"tool": t["tool"], "input": t["input"]} for t in hi.get("trace", [])],
        }
    except Exception as e:
        return {"historian": f"[Historian Fehler: {e}]", "historian_trace": []}


@app.get("/memory/recent")
def memory_recent(limit: int = 10):
    return recent_analyses(limit)


@app.get("/entity")
def entity(q: str, limit: int = 5):
    return find_entity(q, limit=limit)


@app.get("/subgraph")
def subgraph(center_id: str | None = None, depth: int = 2, limit: int = 100):
    """Return nodes and edges — all if no center, else n-hop neighborhood."""
    g = get_graph()

    if center_id:
        node_q = """
        MATCH (center:Entity {id: $cid})
        OPTIONAL MATCH p = (center)-[:DEPENDS_ON*0..$d]-(n:Entity)
        WITH DISTINCT n WHERE n IS NOT NULL
        RETURN n.id, n.name, n.type, n.ticker LIMIT $lim
        """.replace("$d", str(int(depth)))
        edge_q = """
        MATCH (center:Entity {id: $cid})
        MATCH (center)-[:DEPENDS_ON*0..$d]-(:Entity)
        WITH center
        MATCH (a:Entity)-[r:DEPENDS_ON]->(b:Entity)
        WHERE (a = center OR b = center OR
               exists((center)-[:DEPENDS_ON*1..$d]-(a)) OR
               exists((center)-[:DEPENDS_ON*1..$d]-(b)))
        RETURN DISTINCT a.id, b.id, r.criticality, r.substitutability, r.product
        LIMIT $lim
        """.replace("$d", str(int(depth)))
        node_res = g.query(node_q, {"cid": center_id, "lim": limit}).result_set
        edge_res = g.query(edge_q, {"cid": center_id, "lim": limit * 2}).result_set
    else:
        node_res = g.query(
            "MATCH (n:Entity) RETURN n.id, n.name, n.type, n.ticker LIMIT $lim",
            {"lim": limit},
        ).result_set
        edge_res = g.query(
            "MATCH (a:Entity)-[r:DEPENDS_ON]->(b:Entity) "
            "RETURN a.id, b.id, r.criticality, r.substitutability, r.product LIMIT $lim",
            {"lim": limit * 2},
        ).result_set

    nodes = [
        {"id": r[0], "name": r[1], "type": r[2], "ticker": r[3] or ""}
        for r in node_res
    ]
    edges = [
        {
            "source": r[0],
            "target": r[1],
            "criticality": r[2],
            "substitutability": r[3],
            "product": r[4] or "",
        }
        for r in edge_res
    ]
    return {"nodes": nodes, "edges": edges}


@app.get("/")
def root():
    return {"ok": True, "service": "shockwave", "model": os.environ.get("NEBIUS_MODEL", "?")}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.server:app", host="0.0.0.0", port=8000, reload=True)
