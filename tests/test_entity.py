"""Full-text entity resolution tests."""
from tests.conftest import needs_db


@needs_db
def test_find_tsmc_exact():
    from src.graph.entity import find_entity
    results = find_entity("TSMC")
    assert any(r["name"] == "TSMC" for r in results)


@needs_db
def test_find_entity_returns_type():
    from src.graph.entity import find_entity
    results = find_entity("Apple")
    assert results
    assert results[0]["type"] in {"Company", "Supplier", "Resource", "Region", "Facility"}


@needs_db
def test_find_entity_empty_for_gibberish():
    from src.graph.entity import find_entity
    results = find_entity("zzzxxxyyy_nonexistent_qq")
    assert results == []
