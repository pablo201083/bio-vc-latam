"""Find startups still untagged and not yet in entity_enrichments.csv."""
import csv, pathlib, sqlite3

ROOT = pathlib.Path(__file__).resolve().parent.parent
out = ROOT / "staging" / "entity_enrichments.csv"
done = set(r["entity_id"] for r in csv.DictReader(open(out, encoding="utf-8"))
           if r["field_name"] == "bio_lens_tags")

conn = sqlite3.connect(ROOT / "db" / "bio_latam.db")
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
""").fetchall()
conn.close()

remaining = [r for r in rows if r[0] not in done]
print(f"Total untagged in DB: {len(rows)}")
print(f"Already in CSV: {len(done)}")
print(f"Still remaining: {len(remaining)}")
for sid, name, cc, summary, theme in remaining:
    print(f"{sid} | {name} ({cc}) | {theme[:30]} | {summary[:70]}")
