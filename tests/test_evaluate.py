"""End-to-end evaluation — must find >= 15/20 ground-truth SPOFs."""
from tests.conftest import needs_db


@needs_db
def test_recall_at_5_meets_threshold():
    """The headline metric. Threshold set conservatively so we don't fail on
    small data drift; actual observed value is 17/20."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scripts.evaluate import evaluate

    result = evaluate(k_values=[5, 10])
    recall_at_5 = result["hits"][5]
    assert recall_at_5 >= 15, (
        f"Recall@5 is {recall_at_5}/20, expected >= 15 "
        "(did seed data lose important edges?)"
    )
