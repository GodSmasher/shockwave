"""Reverse mode: find hidden single points of failure for a target company.

A "hidden SPOF" sits upstream of the target through 2+ hops of DEPENDS_ON and
has high aggregated impact. These are the risks a Tier-1-only risk register misses.
"""
from src.graph.connection import get_graph


REVERSE_QUERY = """
MATCH (target:Entity {id: $target_id})
MATCH path = (target)-[:DEPENDS_ON*1..$max_hops]->(upstream:Entity)
WITH target, upstream, path,
     reduce(score = 1.0, r IN relationships(path) |
       score * r.criticality * (1.0 - r.substitutability)) AS path_impact,
     length(path) AS hops
WHERE path_impact > 0.01
WITH upstream, min(hops) AS min_hops, sum(path_impact) AS agg_impact,
     count(path) AS path_count,
     collect(DISTINCT [n IN nodes(path) | n.name])[0..3] AS sample_paths
WITH upstream, min_hops, agg_impact, path_count, sample_paths,
     CASE WHEN min_hops >= 2 THEN 1.5 ELSE 0.4 END AS depth_factor
WITH upstream, min_hops, agg_impact, path_count, sample_paths,
     agg_impact * depth_factor AS hidden_score
WHERE hidden_score > 0.03
RETURN
  upstream.id       AS id,
  upstream.name     AS name,
  upstream.type     AS type,
  min_hops,
  round(agg_impact * 10000) / 10000.0 AS aggregated_impact,
  round(hidden_score * 10000) / 10000.0 AS hidden_score,
  path_count,
  sample_paths
ORDER BY hidden_score DESC
LIMIT $limit
"""


def find_hidden_spofs(target_id: str, max_hops: int = 3, limit: int = 10) -> list[dict]:
    g = get_graph()
    query = REVERSE_QUERY.replace("$max_hops", str(int(max_hops)))
    res = g.query(query, {"target_id": target_id, "limit": limit})
    return [
        {
            "id": row[0],
            "name": row[1],
            "type": row[2],
            "min_hops": row[3],
            "aggregated_impact": row[4],
            "hidden_score": row[5],
            "path_count": row[6],
            "sample_paths": row[7],
        }
        for row in res.result_set
    ]


if __name__ == "__main__":
    import json
    import hashlib
    apple_id = hashlib.md5("apple".encode()).hexdigest()[:12]
    print(f"Hidden SPOFs for Apple (id={apple_id}):")
    print(json.dumps(find_hidden_spofs(apple_id), indent=2))
