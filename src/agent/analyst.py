"""Analyst agent: the primary voice. Reasons about supply-chain shocks.

Uses Nebius AI Studio (OpenAI-compatible) with tool/function calling.
"""
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

from src.graph.entity import find_entity
from src.graph.cascade import simulate_shock
from src.graph.reverse import find_hidden_spofs
from src.graph.memory import record_question, record_analysis

load_dotenv()

MODEL = os.environ.get("NEBIUS_MODEL", "meta-llama/Llama-3.3-70B-Instruct")

SYSTEM_PROMPT = """You are a supply-chain risk analyst. You answer questions about \
supply-chain exposure by traversing a FalkorDB graph that connects companies, \
suppliers, resources, regions, and facilities.

Process:
1. Use find_entity to identify the relevant node(s).
2. Depending on the question:
   - simulate_shock (forward: what breaks if X fails?)
   - find_hidden_spofs (reverse: which hidden risks does company Y carry?)
3. Answer in English. Name every company and explain WHY the impact is high.
4. Do NOT invent companies or numbers. If the graph returns nothing, say so.

Format of the final answer:
- One-sentence core finding.
- 3-5 bullet points with specific companies and impact scores.
- For reverse mode: explicitly flag "hidden" SPOFs (min_hops >= 2).
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "find_entity",
            "description": "Fuzzy-search for a company, supplier, resource, region or facility by name. Returns up to 5 ranked matches with id, name, and type.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Name to search for, e.g. 'TSMC' or 'Apple' or 'cobalt'"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "simulate_shock",
            "description": "FORWARD cascade: given a shocked entity id, propagate the impact to all downstream companies with scored multi-hop paths.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_id": {"type": "string", "description": "Node id returned by find_entity"},
                    "severity": {"type": "number", "description": "0.0-1.0 initial shock intensity, default 1.0"},
                    "max_hops": {"type": "integer", "description": "Max propagation depth, default 4"},
                },
                "required": ["target_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_hidden_spofs",
            "description": "REVERSE mode: given a company id, find upstream single points of failure — especially the hidden ones (2+ hops away, not direct Tier-1 suppliers). This is the hero query for discovering risks a CFO may not know about.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_id": {"type": "string", "description": "Company node id from find_entity"},
                    "max_hops": {"type": "integer", "description": "Max upstream depth to explore, default 3"},
                },
                "required": ["target_id"],
            },
        },
    },
]


def _run_tool(name: str, args: dict) -> str:
    try:
        if name == "find_entity":
            return json.dumps(find_entity(args["query"], limit=5))
        if name == "simulate_shock":
            return json.dumps(simulate_shock(
                args["target_id"],
                severity=args.get("severity", 1.0),
                max_hops=args.get("max_hops", 4),
            ))
        if name == "find_hidden_spofs":
            return json.dumps(find_hidden_spofs(
                args["target_id"],
                max_hops=args.get("max_hops", 3),
            ))
    except Exception as e:
        return json.dumps({"error": str(e)})
    return json.dumps({"error": f"unknown tool {name}"})


def _get_client() -> OpenAI:
    return OpenAI(
        api_key=os.environ["NEBIUS_API_KEY"],
        base_url=os.environ.get("NEBIUS_BASE_URL", "https://api.studio.nebius.com/v1"),
    )


def _derive_hypotheses(trace: list[dict]) -> tuple[list[dict], list[str]]:
    """From tool outputs, derive compact hypotheses + involved entity ids."""
    hyps: list[dict] = []
    entity_ids: set[str] = set()
    center_name = None
    for t in trace:
        out = t.get("output_full")
        if t["tool"] == "find_entity" and isinstance(out, list) and out:
            center_name = out[0].get("name")
            entity_ids.add(out[0]["id"])
        if t["tool"] == "find_hidden_spofs" and isinstance(out, list):
            for s in out[:3]:
                entity_ids.add(s["id"])
                hyps.append({
                    "claim": f"If {s['name']} fails, {center_name or 'target'} is impacted via {s['min_hops']}-hop path (score {s['hidden_score']}).",
                    "confidence": min(1.0, s["hidden_score"]),
                    "about_entity_ids": [s["id"]],
                })
        if t["tool"] == "simulate_shock" and isinstance(out, list):
            for h in out[:3]:
                entity_ids.add(h["company_id"])
                hyps.append({
                    "claim": f"Shock of {center_name or 'target'} propagates to {h['company']} with impact {h['impact']}.",
                    "confidence": float(h["impact"]),
                    "about_entity_ids": [h["company_id"]],
                })
    return hyps, list(entity_ids)


def analyze(
    user_question: str,
    trace: bool = True,
    write_memory: bool = True,
    on_event=None,
) -> dict:
    """Run the agent loop. Returns {final_text, trace, question_id, analysis_id}.

    on_event: optional callback(event_dict) called for each tool start/end + composing.
    """
    client = _get_client()
    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_question},
    ]
    tool_trace: list[dict] = []
    question_id = record_question(user_question) if write_memory else ""
    if on_event:
        try: on_event({"type": "start", "question": user_question})
        except Exception: pass

    for turn in range(12):
        if on_event:
            try: on_event({"type": "thinking", "turn": turn + 1})
            except Exception: pass
        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.3,
            max_tokens=1500,
        )
        msg = resp.choices[0].message

        if msg.tool_calls:
            # Append assistant turn (model's tool call)
            messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    } for tc in msg.tool_calls
                ],
            })
            # Execute each tool and append result
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except Exception:
                    args = {}
                if on_event:
                    try: on_event({"type": "tool_call", "name": tc.function.name, "input": args})
                    except Exception: pass
                result = _run_tool(tc.function.name, args)
                try:
                    parsed = json.loads(result)
                except Exception:
                    parsed = None
                tool_trace.append({
                    "tool": tc.function.name,
                    "input": args,
                    "output_preview": result[:400],
                    "output_full": parsed,
                })
                if on_event:
                    # concise summary of what was found
                    summary = None
                    if isinstance(parsed, list):
                        if tc.function.name == "find_entity" and parsed:
                            summary = f"found {parsed[0].get('name')} ({parsed[0].get('type')})"
                        elif tc.function.name == "find_hidden_spofs":
                            summary = f"{len(parsed)} SPOFs, {sum(1 for s in parsed if s.get('min_hops',1) >= 2)} hidden"
                        elif tc.function.name == "simulate_shock":
                            summary = f"{len(parsed)} downstream companies impacted"
                        else:
                            summary = f"{len(parsed)} results"
                    try: on_event({"type": "tool_result", "name": tc.function.name, "summary": summary or "ok"})
                    except Exception: pass
                if trace:
                    print(f"  [tool] {tc.function.name}({args}) -> {result[:200]}")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })
            continue

        # No tool calls → final answer
        final_text = msg.content or ""
        analysis_id = ""
        if on_event:
            try: on_event({"type": "composing"})
            except Exception: pass
        if write_memory:
            hyps, eids = _derive_hypotheses(tool_trace)
            analysis_id = record_analysis(
                role="analyst",
                text=final_text,
                question_id=question_id,
                turns=turn + 1,
                confidence=0.75,
                about_entity_ids=eids,
                hypotheses=hyps,
            )
        return {
            "final_text": final_text,
            "trace": tool_trace,
            "turns": turn + 1,
            "question_id": question_id,
            "analysis_id": analysis_id,
        }

    return {
        "final_text": "[max turns reached]",
        "trace": tool_trace,
        "turns": 12,
        "question_id": question_id,
        "analysis_id": "",
    }


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Welche versteckten Risiken hat Apple?"
    print(f"Q: {q}\n")
    result = analyze(q)
    print(f"\n--- Antwort ({result['turns']} Turns) ---")
    print(result["final_text"])
