"""Shared pytest fixtures.

Tests that need the graph will skip if FALKORDB_HOST isn't configured,
so the test suite still runs on a dev machine without the DB.
"""
import os
import hashlib
import pytest
from dotenv import load_dotenv

load_dotenv()


def _has_db() -> bool:
    return bool(os.environ.get("FALKORDB_HOST"))


needs_db = pytest.mark.skipif(not _has_db(), reason="FALKORDB_HOST not set")


def slug(s: str) -> str:
    """Same deterministic id derivation used by load_seed.py."""
    return hashlib.md5(s.lower().strip().encode()).hexdigest()[:12]
