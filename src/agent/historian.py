"""Historian agent — pulls real historical precedents to contextualize current analysis."""
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

from src.graph.history import find_precedents_for_entities, find_precedents_by_type
from src.graph.memory import record_analysis

load_dotenv()

MODEL = os.environ.get("NEBIUS_MODEL", "Qwen/Qwen3-235B-A22B-Instruct-2507")

SYSTEM_PROMPT = """Du bist Supply-Chain-Historiker. Deine Aufgabe: finde \
vergangene reale Events die der aktuellen Analyse ähneln.

Prozess:
1. find_precedents_for_entities(entity_ids) → historische Shocks die diese Firmen trafen.
2. Falls leer: find_precedents_by_type(event_type) für den passenden Typ \
   (shipping_disruption, facility_shutdown, commodity_shock, pandemic, supplier_quality).
3. Antworte auf Deutsch mit 2-3 Präzedenzfällen. PRO FALL:
   - Jahr + Event-Name
   - Was tatsächlich passierte
   - Recovery-Dauer in Tagen/Monaten
   - EIN überraschender Zweitordnungseffekt (nicht offensichtlich)

Keine Analogie erzwingen — "Kein guter Präzedenzfall gefunden" ist gültig.
Ton: nüchtern, Daten-fokussiert, nenne Zahlen. Keine Füllwörter.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "find_precedents_for_entities",
            "description": "Return past real supply-chain shock events that affected any of the given entities.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_ids": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["entity_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_precedents_by_type",
            "description": "Return past events of a given type. Types: shipping_disruption, facility_shutdown, commodity_shock, pandemic, supplier_quality, natural_disaster, facility_disruption.",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_type": {"type": "string"},
                },
                "required": ["event_type"],
            },
        },
    },
]


def _run_tool(name: str, args: dict) -> str:
    try:
        if name == "find_precedents_for_entities":
            return json.dumps(find_precedents_for_entities(args.get("entity_ids", [])))
        if name == "find_precedents_by_type":
            return json.dumps(find_precedents_by_type(args.get("event_type", "")))
    except Exception as e:
        return json.dumps({"error": str(e)})
    return json.dumps({"error": f"unknown tool {name}"})


def _client() -> OpenAI:
    return OpenAI(
        api_key=os.environ["NEBIUS_API_KEY"],
        base_url=os.environ.get("NEBIUS_BASE_URL", "https://api.studio.nebius.com/v1"),
    )


def contextualize(
    analyst_text: str,
    entity_ids: list[str],
    question_id: str,
) -> dict:
    client = _client()
    user_msg = (
        "Analyse des Analysten:\n\n"
        + analyst_text[:1500]
        + "\n\nBetroffene Entity-IDs: " + json.dumps(entity_ids)
        + "\n\nFinde 2-3 reale historische Präzedenzfälle. Nutze die Tools."
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
            temperature=0.3,
            max_tokens=700,
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
                trace.append({"tool": tc.function.name, "input": args, "output_full": parsed})
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
            continue

        final_text = msg.content or ""
        aid = record_analysis(
            role="historian",
            text=final_text,
            question_id=question_id,
            turns=turn + 1,
            confidence=0.7,
            about_entity_ids=entity_ids,
        )
        return {"text": final_text, "analysis_id": aid, "trace": trace}

    return {"text": "[max turns reached]", "analysis_id": "", "trace": trace}
