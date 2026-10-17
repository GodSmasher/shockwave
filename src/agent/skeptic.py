"""Skeptic agent — devil's advocate.

Takes an Analyst analysis + the entities it touched. Queries memory for
contradicting past claims and finds counterexample companies.

Writes its own :Analysis node (role='skeptic') linked by [:CHALLENGED] to
the analyst's analysis. Returns a short text (≤3 bullet points).
"""
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

from src.graph.memory import (
    query_similar_hypotheses,
    find_counterexample_entities,
    record_analysis,
)

load_dotenv()

MODEL = os.environ.get("NEBIUS_MODEL", "Qwen/Qwen3-235B-A22B-Instruct-2507")

SYSTEM_PROMPT = """Du bist ein kritischer Senior-Risk-Analyst. Dein EINZIGER Job: \
die Analyse eines Kollegen angreifen.

Prozess:
1. query_similar_hypotheses(entity_id) → gab es ähnliche Hypothesen die später \
   überoptimistisch oder zu pessimistisch waren?
2. find_counterexamples(entity_id) → gibt es Firmen die ähnliche Dependencies haben, \
   aber Shocks überlebt haben? Das schwächt Doom-Narrative.
3. Antworte in max 3 Punkten auf Deutsch:
   - Welche Annahme der Analyse ist schwach?
   - Welche Daten fehlen?
   - Welche alternative Interpretation existiert?

Ton: direkt, respektvoll, keine Höflichkeitsfloskeln. Wenn die Analyse solide ist, \
sag es in einem Satz. Keine Füllwörter wie "insgesamt" oder "zusammenfassend".
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_similar_hypotheses",
            "description": "Return past Hypothesis nodes about the same entity, so the skeptic can check for prior contradictions or over-claims.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_id": {"type": "string"},
                },
                "required": ["entity_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_counterexamples",
            "description": "Find other Companies that share dependencies with the target entity — potential counterexamples that survived similar shocks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_id": {"type": "string"},
                },
                "required": ["entity_id"],
            },
        },
    },
]


def _run_tool(name: str, args: dict) -> str:
    try:
        if name == "query_similar_hypotheses":
            return json.dumps(query_similar_hypotheses(args["entity_id"]))
        if name == "find_counterexamples":
            return json.dumps(find_counterexample_entities(args["entity_id"]))
    except Exception as e:
        return json.dumps({"error": str(e)})
    return json.dumps({"error": f"unknown tool {name}"})


def _client() -> OpenAI:
    return OpenAI(
        api_key=os.environ["NEBIUS_API_KEY"],
        base_url=os.environ.get("NEBIUS_BASE_URL", "https://api.studio.nebius.com/v1"),
    )


def challenge(
    analyst_text: str,
    entity_ids: list[str],
    question_id: str,
    analyst_analysis_id: str,
) -> dict:
    """Run the skeptic. Returns {text, analysis_id, trace}."""
    client = _client()
    user_msg = (
        "Analyse des Analysten:\n\n"
        + analyst_text[:2000]
        + "\n\nBetroffene Entity-IDs: "
        + json.dumps(entity_ids)
        + "\n\nFinde Schwächen. Nutze die Tools."
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]
    trace: list[dict] = []

    for turn in range(8):
        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.4,
            max_tokens=800,
        )
        msg = resp.choices[0].message

        if msg.tool_calls:
            messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name,
                                  "arguments": tc.function.arguments}}
                    for tc in msg.tool_calls
                ],
            })
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except Exception:
                    args = {}
                result = _run_tool(tc.function.name, args)
                try:
                    parsed = json.loads(result)
                except Exception:
                    parsed = None
                trace.append({
                    "tool": tc.function.name,
                    "input": args,
                    "output_full": parsed,
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })
            continue

        final_text = msg.content or ""
        aid = record_analysis(
            role="skeptic",
            text=final_text,
            question_id=question_id,
            turns=turn + 1,
            confidence=0.6,
            about_entity_ids=entity_ids,
            challenged_analysis_id=analyst_analysis_id,
        )
        return {"text": final_text, "analysis_id": aid, "trace": trace}

    return {"text": "[max turns reached]", "analysis_id": "", "trace": trace}


if __name__ == "__main__":
    # Smoke test: use last analyst analysis
    from src.graph.memory import recent_analyses
    recent = recent_analyses(1)
    if not recent:
        print("No analyst analyses yet — run analyst first.")
    else:
        a = recent[0]
        print(f"Challenging: {a['question']}")
        result = challenge(
            analyst_text="Nvidia hängt kritisch von TSMC ab.",
            entity_ids=[],
            question_id="dummy",
            analyst_analysis_id="dummy",
        )
        print(result["text"])
