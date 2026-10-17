"""Entity resolution via FalkorDB full-text index on :Entity."""
from src.graph.connection import get_graph


def find_entity(query: str, limit: int = 5) -> list[dict]:
    g = get_graph()
    results: list[dict] = []

    try:
        res = g.query(
            "CALL db.idx.fulltext.queryNodes('Entity', $q) YIELD node, score "
            "RETURN node.id, node.name, node.type, score "
            "ORDER BY score DESC LIMIT $lim",
            {"q": query, "lim": limit},
        )
        for row in res.result_set:
            results.append({
                "id": row[0],
                "name": row[1],
                "type": row[2],
                "score": row[3],
            })
    except Exception:
        pass

    if not results:
        res = g.query(
            "MATCH (n:Entity) WHERE toLower(n.name) CONTAINS toLower($q) "
            "RETURN n.id, n.name, n.type LIMIT $lim",
            {"q": query, "lim": limit},
        )
        for row in res.result_set:
            results.append({
                "id": row[0],
                "name": row[1],
                "type": row[2],
                "score": 1.0,
            })

    return results[:limit]


if __name__ == "__main__":
    import json
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "TSMC"
    print(json.dumps(find_entity(q), indent=2))
