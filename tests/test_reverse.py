"""Integration tests for reverse-mode hidden SPOF detection."""
from tests.conftest import needs_db, slug


@needs_db
def test_apple_finds_asml_at_two_hops():
    """The flagship Shockwave finding: Apple → TSMC → ASML."""
    from src.graph.reverse import find_hidden_spofs
    spofs = find_hidden_spofs(slug("Apple"), max_hops=3, limit=10)
    asml = next((s for s in spofs if s["name"] == "ASML"), None)
    assert asml is not None, "ASML should be surfaced for Apple"
    assert asml["min_hops"] == 2
    assert asml["sample_paths"][0] == ["Apple", "TSMC", "ASML"]


@needs_db
def test_apple_finds_zeiss_at_three_hops():
    """The 3-hop hidden SPOF — Carl Zeiss SMT via TSMC via ASML."""
    from src.graph.reverse import find_hidden_spofs
    spofs = find_hidden_spofs(slug("Apple"), max_hops=4, limit=15)
    zeiss = next((s for s in spofs if s["name"] == "Carl Zeiss SMT"), None)
    assert zeiss is not None, "Carl Zeiss SMT should be surfaced"
    assert zeiss["min_hops"] == 3


@needs_db
def test_hidden_score_outranks_tier1():
    """Our hero: a 2-hop with high aggregated impact should outrank a direct Tier-1
    with lower criticality × substitutability."""
    from src.graph.reverse import find_hidden_spofs
    spofs = find_hidden_spofs(slug("Apple"), max_hops=3, limit=10)
    # Top result should be a 2+ hop (hidden) one
    assert spofs[0]["min_hops"] >= 2


@needs_db
def test_reverse_returns_structured_data():
    from src.graph.reverse import find_hidden_spofs
    spofs = find_hidden_spofs(slug("Apple"))
    for s in spofs:
        assert set(s.keys()) >= {
            "id", "name", "type", "min_hops",
            "aggregated_impact", "hidden_score", "sample_paths",
        }
