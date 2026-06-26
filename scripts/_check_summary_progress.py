"""Check how many summaries still need work."""
import sqlite3, csv, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
conn = sqlite3.connect(ROOT / "db" / "bio_latam.db")

# How many include startups have good summaries (>= 80 chars)
total = conn.execute("SELECT COUNT(*) FROM startup_extended WHERE scope_decision='include'").fetchone()[0]
with_good = conn.execute("""
    SELECT COUNT(*) FROM startup_extended sx
    WHERE sx.scope_decision='include'
      AND sx.startup_summary_en IS NOT NULL
      AND LENGTH(sx.startup_summary_en) >= 80
""").fetchone()[0]
with_any = conn.execute("""
    SELECT COUNT(*) FROM startup_extended sx
    WHERE sx.scope_decision='include'
      AND sx.startup_summary_en IS NOT NULL
      AND LENGTH(sx.startup_summary_en) > 0
""").fetchone()[0]

print(f"Include startups: {total}")
print(f"  Con summary_en >= 80 chars: {with_good}")
print(f"  Con summary_en (cualquier): {with_any}")
print(f"  Sin summary_en: {total - with_any}")

# How many have tags
with_tags = conn.execute("""
    SELECT COUNT(*) FROM startup_extended
    WHERE scope_decision='include'
      AND bio_lens_tags IS NOT NULL AND bio_lens_tags != ''
""").fetchone()[0]
print(f"\nCon bio_lens_tags: {with_tags}/{total}")

# Founded year coverage
with_year = conn.execute("""
    SELECT COUNT(*) FROM entities e
    JOIN startup_extended sx ON sx.startup_id = e.entity_id
    WHERE sx.scope_decision='include'
      AND e.founded_year IS NOT NULL
""").fetchone()[0]
print(f"Con founded_year: {with_year}/{total}")

conn.close()
