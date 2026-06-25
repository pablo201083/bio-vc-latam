"""Fetch untagged startups in batches for inline tag assignment."""
import sqlite3, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
conn = sqlite3.connect(ROOT / "db" / "bio_latam.db")
offset = int(sys.argv[1]) if len(sys.argv) > 1 else 0
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 25

rows = conn.execute("""
    SELECT sx.startup_id, e.canonical_name, e.country_code,
           coalesce(sx.startup_summary_en, sx.startup_summary_v1, sx.business_one_liner, '') as summary,
           coalesce(sx.macro_theme, sx.bio_theme_primary, '') as theme
    FROM startup_extended sx
    JOIN entities e ON e.entity_id = sx.startup_id
    WHERE sx.scope_decision = 'include'
      AND (sx.bio_lens_tags IS NULL OR sx.bio_lens_tags = '')
      AND (sx.domain_tags IS NULL OR sx.domain_tags = '')
    ORDER BY e.canonical_name
    LIMIT ? OFFSET ?
""", (limit, offset)).fetchall()
conn.close()

for sid, name, cc, summary, theme in rows:
    print(f"{sid} | {name} ({cc}) | {theme} | {summary[:100]}")
