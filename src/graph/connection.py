"""FalkorDB connection singleton + graph accessor."""
import os
from functools import lru_cache
from falkordb import FalkorDB
from dotenv import load_dotenv

load_dotenv()


@lru_cache(maxsize=1)
def get_db() -> FalkorDB:
    host = os.environ["FALKORDB_HOST"]
    port = int(os.environ.get("FALKORDB_PORT", 6379))
    password = os.environ.get("FALKORDB_PASSWORD") or None
    username = os.environ.get("FALKORDB_USERNAME") or None
    return FalkorDB(host=host, port=port, username=username, password=password)


def get_graph(name: str | None = None):
    name = name or os.environ.get("FALKORDB_GRAPH", "shockwave")
    return get_db().select_graph(name)


def query(cypher: str, params: dict | None = None):
    g = get_graph()
    return g.query(cypher, params or {})
