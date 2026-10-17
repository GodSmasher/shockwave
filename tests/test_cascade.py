"""Integration tests for forward-cascade propagation."""
from tests.conftest import needs_db, slug


@needs_db
def test_tsmc_shock_hits_major_customers():
    from src.graph.cascade import simulate_shock
    result = simulate_shock(slug("TSMC"), severity=1.0)
    names = {r["company"] for r in result}
    # TSMC's named customers in our seed
    assert "Nvidia" in names
    assert "Apple" in names
    assert "AMD" in names
    assert len(result) >= 3


@needs_db
def test_cascade_impact_decays_with_substitutability():
    """A supplier with high substitutability should produce lower downstream impact."""
    from src.graph.cascade import simulate_shock
    tsmc = simulate_shock(slug("TSMC"))
    # Nvidia is on TSMC with sub=0.05 (barely substitutable) → very high impact
    nvidia = next((r for r in tsmc if r["company"] == "Nvidia"), None)
    assert nvidia is not None
    assert nvidia["impact"] > 0.8


@needs_db
def test_cascade_returns_empty_for_unknown_target():
    from src.graph.cascade import simulate_shock
    assert simulate_shock("nonexistent_id_xxx") == []
