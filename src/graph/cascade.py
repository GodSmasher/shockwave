"""Forward cascade simulation.

Impact = severity * product over path of criticality * (1 - substitutability).
"""
from src.graph.connection import get_graph


CASCADE_QUERY = """
MATCH (target:Entity {id: $target_id})
MATCH p = (target)<-[:DEPENDS_ON*1..$max_hops]-(c:Entity)
WHERE c.type = 'Company'
WITH c, p,
     reduce(score = $severity, r IN relationships(p) |
       score * r.criticality * (1.0 - r.substitutability)) AS impact
WHERE impact > $threshold
WITH c, impact, length(p) AS hops,
     [n IN nodes(p) | n.name] AS chain
RETURN c.id AS company_id, c.name AS company, c.ticker AS ticker,
       impact, hops, chain
ORDER BY impact DESC
LIMIT $limit
"""


def simulate_shock(
    target_id: str,
    severity: float = 1.0,
    max_hops: int = 4,
    threshold: float = 0.05,
    limit: int = 25,
) -> list[dict]:
    g = get_graph()
    query = CASCADE_QUERY.replace("$max_hops", str(int(max_hops)))
    res = g.query(query, {
        "target_id": target_id,
        "severity": severity,
        "threshold": threshold,
        "limit": limit,
    })
    return [
        {
            "company_id": row[0],
            "company": row[1],
            "ticker": row[2],
            "impact": round(row[3], 4),
            "hops": row[4],
            "chain": row[5],
        }
        for row in res.result_set
    ]


if __name__ == "__main__":
    import json
    import hashlib
    tsmc_id = hashlib.md5("tsmc".encode()).hexdigest()[:12]
    print(f"Shock TSMC id={tsmc_id}")
    print(json.dumps(simulate_shock(tsmc_id, severity=1.0), indent=2))
