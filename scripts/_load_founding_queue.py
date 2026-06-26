"""Load startups missing founded_year that have a real website URL."""
import sqlite3, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
conn = sqlite3.connect(ROOT / "db" / "bio_latam.db")
rows = conn.execute("""
    SELECT sx.startup_id, e.canonical_name, e.country_code, e.website
    FROM startup_extended sx
    JOIN entities e ON e.entity_id = sx.startup_id
    WHERE sx.scope_decision = 'include'
      AND e.founded_year IS NULL
      AND e.website IS NOT NULL AND e.website LIKE 'http%'
    ORDER BY e.canonical_name
""").fetchall()
conn.close()
print(f"Total sin founding_year con URL: {len(rows)}")
for sid, name, cc, url in rows:
    print(f"{sid}|{name}|{cc}|{url}")
