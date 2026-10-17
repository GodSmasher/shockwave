"""Create indexes + constraints for the shockwave graph.

Design decision: all WORLD nodes use a single :Entity label with a `type` property
(Company | Supplier | Resource | Region | Facility). This way:
  - TSMC is ONE node whether it appears as buyer (of ASML) or target (of Apple).
  - Multi-hop traversal with [:DEPENDS_ON*] actually works.
  - Full-text search spans everything in one index.

Memory nodes use their own labels (Question, Analysis, Hypothesis, NewsEvent).
"""
from src.graph.connection import get_graph

MEMORY_LABELS = ["Question", "Analysis", "Hypothesis", "NewsEvent", "UserSession"]


def init_schema() -> None:
    g = get_graph()

    # Uniqueness index on Entity.id
    try:
        g.query("CREATE INDEX FOR (n:Entity) ON (n.id)")
    except Exception as e:
        if "already indexed" not in str(e).lower():
            print(f"  warn [Entity.id]: {e}")

    # Memory label indexes
    for label in MEMORY_LABELS:
        try:
            g.query(f"CREATE INDEX FOR (n:{label}) ON (n.id)")
        except Exception as e:
            if "already indexed" not in str(e).lower():
                print(f"  warn [{label}.id]: {e}")

    # Full-text index on Entity.name (fuzzy resolution)
    try:
        g.query("CALL db.idx.fulltext.createNodeIndex('Entity', 'name')")
    except Exception as e:
        if "already indexed" not in str(e).lower() and "exists" not in str(e).lower():
            print(f"  warn [Entity fulltext]: {e}")

    print("Schema initialized.")


if __name__ == "__main__":
    init_schema()
