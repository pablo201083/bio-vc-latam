import sqlite3

import pytest

from conftest import DB_PATH
from src.vocabularies import BIO_THEMES

pytestmark = pytest.mark.skipif(
    not DB_PATH.exists(), reason="db/bio_latam.db not present (not tracked in git)"
)


@pytest.fixture
def conn():
    c = sqlite3.connect(str(DB_PATH))
    yield c
    c.close()


def test_investment_edges_no_duplicate_investor_startup_stage(conn):
    rows = conn.execute(
        "SELECT investor_id, startup_id, COALESCE(round_stage, '') FROM investment_edges"
    ).fetchall()
    seen = set()
    dupes = []
    for row in rows:
        if row in seen:
            dupes.append(row)
        seen.add(row)
    assert not dupes, f"duplicate (investor_id, startup_id, round_stage) pairs: {dupes[:10]}"


def test_includes_bio_theme_primary_in_bio_themes(conn):
    rows = conn.execute(
        """
        SELECT startup_id, bio_theme_primary FROM startup_extended
        WHERE scope_decision = 'include' AND bio_theme_primary IS NOT NULL
              AND bio_theme_primary != ''
        """
    ).fetchall()
    bad = [(sid, theme) for sid, theme in rows if theme not in BIO_THEMES]
    assert not bad, f"includes with bio_theme_primary outside BIO_THEMES: {bad[:10]}"


def test_investment_edges_investor_id_has_entity_row(conn):
    rows = conn.execute(
        """
        SELECT ie.investor_id FROM investment_edges ie
        LEFT JOIN entities e ON e.entity_id = ie.investor_id
        WHERE e.entity_id IS NULL
        """
    ).fetchall()
    assert not rows, f"investment_edges.investor_id with no entities row: {rows[:10]}"
