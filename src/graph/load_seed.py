"""Load the 50-edge seed CSV into FalkorDB.

All world nodes are :Entity with a type property. One TSMC node, period.
"""
import csv
import hashlib
import re
from pathlib import Path
from src.graph.connection import get_graph

SEED_PATH = Path(__file__).resolve().parents[2] / "data" / "seed_dependencies.csv"


def slug(s: str) -> str:
    return hashlib.md5(s.lower().strip().encode()).hexdigest()[:12]


def normalize_target(raw: str) -> tuple[str, str | None]:
    """Split 'TSMC - A/M-series SoCs' into ('TSMC', 'A/M-series SoCs')."""
    s = raw.strip()
    for sep in [" - ", " – "]:
        if sep in s:
            head, tail = s.split(sep, 1)
            return head.strip(), tail.strip()
    m = re.match(r"^([^()]+?)\s*\(([^)]+)\)\s*$", s)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return s, None


def reset_graph() -> None:
    g = get_graph()
    g.query("MATCH (n) DETACH DELETE n")


def load_seed(reset: bool = True) -> None:
    g = get_graph()

    if reset:
        print("Resetting graph...")
        reset_graph()

    with SEED_PATH.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"Loading {len(rows)} seed edges...")

    for r in rows:
        buyer_name = r["buyer"].strip()
        buyer_ticker = (r.get("buyer_ticker") or "").strip()
        buyer_id = slug(buyer_name)

        raw_target = r["target"].strip()
        canonical, product = normalize_target(raw_target)
        target_id = slug(canonical)
        target_type = r["target_type"].strip().capitalize()  # Supplier / Resource / Region / Facility

        criticality = float(r["criticality"])
        substitutability = float(r["substitutability"])
        notes = r["notes"]
        source = r["source"]

        # Buyer: always Entity + type=Company (ticker optional)
        g.query(
            "MERGE (c:Entity {id: $id}) "
            "SET c.name = $name, c.type = 'Company', c.ticker = $ticker",
            {"id": buyer_id, "name": buyer_name, "ticker": buyer_ticker},
        )

        # Target: Entity + type = Supplier/Resource/Region/Facility
        # Don't downgrade a Company node to Supplier if it already exists.
        g.query(
            "MERGE (t:Entity {id: $id}) "
            "ON CREATE SET t.name = $name, t.type = $type "
            "ON MATCH SET t.name = coalesce(t.name, $name)",
            {"id": target_id, "name": canonical, "type": target_type},
        )

        # Edge
        g.query(
            "MATCH (c:Entity {id: $buyer_id}), (t:Entity {id: $target_id}) "
            "CREATE (c)-[d:DEPENDS_ON {"
            "  criticality: $crit, substitutability: $sub, "
            "  product: $product, notes: $notes, source: $source"
            "}]->(t)",
            {
                "buyer_id": buyer_id,
                "target_id": target_id,
                "crit": criticality,
                "sub": substitutability,
                "product": product or "",
                "notes": notes,
                "source": source,
            },
        )

    # Stats
    res = g.query("MATCH (n:Entity) RETURN n.type AS type, count(n) AS n ORDER BY n DESC")
    print("Entity nodes by type:")
    for row in res.result_set:
        print(f"  {row[0]:12s}: {row[1]}")

    res = g.query("MATCH ()-[r:DEPENDS_ON]->() RETURN count(r) AS n")
    print(f"DEPENDS_ON edges: {res.result_set[0][0]}")

    # Sanity A: TSMC customers
    res = g.query(
        "MATCH (c:Entity)-[d:DEPENDS_ON]->(s:Entity {name: 'TSMC'}) "
        "RETURN c.name, d.product, d.criticality ORDER BY d.criticality DESC"
    )
    print("\nTSMC customers:")
    for row in res.result_set:
        print(f"  {row[0]:20s} -> {row[1]} (crit={row[2]})")

    # Sanity B: TSMC's own suppliers (multi-hop test)
    res = g.query(
        "MATCH (s:Entity {name: 'TSMC'})-[d:DEPENDS_ON]->(t:Entity) "
        "RETURN t.name, d.product, d.criticality"
    )
    print("\nTSMC's own dependencies (confirms multi-hop will work):")
    for row in res.result_set:
        print(f"  TSMC -> {row[0]:20s} ({row[1]}, crit={row[2]})")


if __name__ == "__main__":
    load_seed(reset=True)
