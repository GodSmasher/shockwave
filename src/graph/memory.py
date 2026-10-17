"""Memory writes to the shockwave graph.

Each analyst run produces:
  (:Question {id, text, ts})
  (:Analysis {id, role: 'analyst', text, confidence, turns, ts})
     -[:ANSWERED]-> (:Question)
     -[:CONCLUDED {confidence}]-> (:Hypothesis {claim, confidence})
     -[:ABOUT]-> (:Entity)                     # the subject node
     -[:CITES]-> (:Spof)                       # the top-ranked finding

Skeptic / historian runs append (:Analysis {role:'skeptic'|'historian'}) linked
by [:CHALLENGED] / [:CITES] to the originating analysis.
"""
import hashlib
import json
import time
import uuid
from src.graph.connection import get_graph


def _id() -> str:
    return uuid.uuid4().hex[:16]


def _now_ms() -> int:
    return int(time.time() * 1000)


def record_question(text: str) -> str:
    g = get_graph()
    qid = _id()
    g.query(
        "CREATE (q:Question {id: $id, text: $text, ts: $ts})",
        {"id": qid, "text": text, "ts": _now_ms()},
    )
    return qid


def record_analysis(
    role: str,
    text: str,
    question_id: str,
    turns: int,
    confidence: float = 0.7,
    about_entity_ids: list[str] | None = None,
    hypotheses: list[dict] | None = None,
    challenged_analysis_id: str | None = None,
) -> str:
    """Store an analyst/skeptic/historian analysis + its hypotheses."""
    g = get_graph()
    aid = _id()

    g.query(
        "MATCH (q:Question {id: $qid}) "
        "CREATE (a:Analysis {id: $aid, role: $role, text: $text, "
        "  confidence: $conf, turns: $turns, ts: $ts})-[:ANSWERED]->(q)",
        {
            "aid": aid, "qid": question_id, "role": role, "text": text[:4000],
            "conf": confidence, "turns": turns, "ts": _now_ms(),
        },
    )

    if challenged_analysis_id:
        g.query(
            "MATCH (a:Analysis {id: $aid}), (prev:Analysis {id: $prev}) "
            "CREATE (a)-[:CHALLENGED]->(prev)",
            {"aid": aid, "prev": challenged_analysis_id},
        )

    for eid in about_entity_ids or []:
        g.query(
            "MATCH (a:Analysis {id: $aid}), (e:Entity {id: $eid}) "
            "CREATE (a)-[:ABOUT]->(e)",
            {"aid": aid, "eid": eid},
        )

    for h in hypotheses or []:
        hid = _id()
        g.query(
            "MATCH (a:Analysis {id: $aid}) "
            "CREATE (h:Hypothesis {id: $hid, claim: $claim, "
            "  confidence: $conf, ts: $ts})"
            "<-[:CONCLUDED {confidence: $conf}]-(a)",
            {
                "aid": aid, "hid": hid, "claim": h.get("claim", "")[:500],
                "conf": float(h.get("confidence", 0.5)), "ts": _now_ms(),
            },
        )
        for eid in h.get("about_entity_ids", []):
            g.query(
                "MATCH (h:Hypothesis {id: $hid}), (e:Entity {id: $eid}) "
                "CREATE (h)-[:ABOUT]->(e)",
                {"hid": hid, "eid": eid},
            )
    return aid


def query_similar_hypotheses(entity_id: str, limit: int = 5) -> list[dict]:
    """For a given entity, return past hypotheses that touched it."""
    g = get_graph()
    res = g.query(
        "MATCH (e:Entity {id: $eid})<-[:ABOUT]-(h:Hypothesis)<-[:CONCLUDED]-(a:Analysis) "
        "RETURN h.id, h.claim, h.confidence, a.role, a.ts "
        "ORDER BY a.ts DESC LIMIT $lim",
        {"eid": entity_id, "lim": limit},
    )
    return [
        {"id": r[0], "claim": r[1], "confidence": r[2], "role": r[3], "ts": r[4]}
        for r in res.result_set
    ]


def recent_analyses(limit: int = 10) -> list[dict]:
    """Memory timeline for UI."""
    g = get_graph()
    res = g.query(
        "MATCH (a:Analysis)-[:ANSWERED]->(q:Question) "
        "OPTIONAL MATCH (a)-[:ABOUT]->(e:Entity) "
        "WITH a, q, collect(DISTINCT e.name)[0..3] AS entities "
        "RETURN a.id, a.role, a.ts, a.confidence, a.turns, q.text, entities "
        "ORDER BY a.ts DESC LIMIT $lim",
        {"lim": limit},
    )
    return [
        {
            "id": r[0], "role": r[1], "ts": r[2], "confidence": r[3],
            "turns": r[4], "question": r[5], "entities": r[6] or [],
        }
        for r in res.result_set
    ]


def find_counterexample_entities(entity_id: str, limit: int = 5) -> list[dict]:
    """Find Companies that depend on the same upstream nodes but seem resilient
    (fewer SPOFs). Useful for Skeptic to challenge Analyst's doom scenarios."""
    g = get_graph()
    res = g.query(
        "MATCH (target:Entity {id: $eid})-[:DEPENDS_ON]->(upstream:Entity) "
        "MATCH (other:Entity {type: 'Company'})-[:DEPENDS_ON]->(upstream) "
        "WHERE other.id <> target.id "
        "WITH other, count(DISTINCT upstream) AS shared "
        "RETURN other.id, other.name, shared "
        "ORDER BY shared DESC LIMIT $lim",
        {"eid": entity_id, "lim": limit},
    )
    return [
        {"id": r[0], "name": r[1], "shared_dependencies": r[2]}
        for r in res.result_set
    ]
