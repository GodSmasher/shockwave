"""Unit tests for seed-row normalization — no DB needed."""
from src.graph.load_seed import normalize_target


def test_normalize_dash_product():
    name, product = normalize_target("TSMC - A/M-series SoCs")
    assert name == "TSMC"
    assert product == "A/M-series SoCs"


def test_normalize_endash():
    name, product = normalize_target("ASML – EUV scanners")
    assert name == "ASML"
    assert product == "EUV scanners"


def test_normalize_parens():
    name, product = normalize_target("Catalent (US/EU plants)")
    assert name == "Catalent"
    assert product == "US/EU plants"


def test_normalize_bare():
    name, product = normalize_target("Pilbara Minerals")
    assert name == "Pilbara Minerals"
    assert product is None


def test_normalize_strips_whitespace():
    name, _ = normalize_target("  TSMC   ")
    assert name == "TSMC"
