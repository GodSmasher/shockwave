"""Historical precedent lookup.

Static CSV of real supply-chain shock events, indexed and queryable by entity.
Loaded into graph as :NewsEvent nodes so Cypher can join them with the world.
"""
import csv
from pathlib import Path
from src.graph.connection import get_graph

HIST_PATH = Path(__file__).resolve().parents[2] / "data" / "historical_events.csv"


def load_history() -> int:
    g = get_graph()
    with HIST_PATH.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    for r in rows:
        affected = [a.strip() for a in r["affected_entities"].split(",") if a.strip()]
        g.query(
            "MERGE (n:NewsEvent {id: $id}) "
            "SET n.event = $event, n.year = $year, n.event_type = $type, "
            "    n.recovery_days = $rec, n.impact_summary = $imp",
            {
                "id": r["id"],
                "event": r["event"],
                "year": int(r["year"]),
                "type": r["event_type"],
                "rec": int(r["recovery_days"]),
                "imp": r["impact_summary"],
            },
        )
        # Link to any Entity whose name matches
        for name in affected:
            g.query(
                "MATCH (n:NewsEvent {id: $id}), (e:Entity) "
                "WHERE e.name = $name "
                "MERGE (n)-[:AFFECTED {ts: n.year}]->(e)",
                {"id": r["id"], "name": name},
            )

    res = g.query("MATCH (n:NewsEvent) RETURN count(n)")
    count = res.result_set[0][0]
    res2 = g.query("MATCH (:NewsEvent)-[r:AFFECTED]->() RETURN count(r)")
    linked = res2.result_set[0][0]
    print(f"Loaded {count} historical events, {linked} entity links.")
    return count


def find_precedents_for_entities(entity_ids: list[str], limit: int = 5) -> list[dict]:
    """Return past NewsEvents that touched any of the given entities."""
    g = get_graph()
    if not entity_ids:
        return []
    res = g.query(
        "MATCH (e:Entity) WHERE e.id IN $ids "
        "MATCH (n:NewsEvent)-[:AFFECTED]->(e) "
        "RETURN DISTINCT n.id, n.event, n.year, n.event_type, "
        "       n.recovery_days, n.impact_summary, "
        "       collect(DISTINCT e.name) AS entities "
        "ORDER BY n.year DESC LIMIT $lim",
        {"ids": entity_ids, "lim": limit},
    )
    return [
        {
            "id": r[0], "event": r[1], "year": r[2], "event_type": r[3],
            "recovery_days": r[4], "impact_summary": r[5], "entities": r[6],
        }
        for r in res.result_set
    ]


def find_precedents_by_type(event_type: str, limit: int = 5) -> list[dict]:
    g = get_graph()
    res = g.query(
        "MATCH (n:NewsEvent {event_type: $t}) "
        "RETURN n.id, n.event, n.year, n.recovery_days, n.impact_summary "
        "ORDER BY n.year DESC LIMIT $lim",
        {"t": event_type, "lim": limit},
    )
    return [
        {"id": r[0], "event": r[1], "year": r[2], "recovery_days": r[3], "impact_summary": r[4]}
        for r in res.result_set
    ]


if __name__ == "__main__":
    load_history()
