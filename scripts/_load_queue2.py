"""Load next batch of high-risk startups for summary writing."""
import csv, pathlib, sqlite3, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
done_file = ROOT / "staging" / "entity_enrichments.csv"

done_summaries = set(
    r["entity_id"] for r in csv.DictReader(open(done_file, encoding="utf-8"))
    if r["field_name"] == "startup_summary_en"
)

conn = sqlite3.connect(ROOT / "db" / "bio_latam.db")
rows = conn.execute("""
    SELECT sx.startup_id, e.canonical_name, e.country_code,
           e.website,
           coalesce(sx.startup_summary_en, '') as summary_en,
           coalesce(sx.startup_summary_v1, '') as summary_v1,
           coalesce(sx.business_one_liner, '') as one_liner,
           coalesce(sx.macro_theme, sx.bio_theme_primary, '') as theme
    FROM startup_extended sx
    JOIN entities e ON e.entity_id = sx.startup_id
    WHERE sx.scope_decision = 'include'
      AND (sx.startup_summary_en IS NULL OR length(sx.startup_summary_en) < 100)
    ORDER BY sx.cluster_confidence ASC
""").fetchall()
conn.close()

remaining = [r for r in rows if r[0] not in done_summaries]
print(f"Remaining high-risk without summary: {len(remaining)}")
for sid, name, cc, url, sum_en, sum_v1, liner, theme in remaining[:50]:
    has_url = "YES" if url and url.startswith("http") else "NO"
    print(f"{sid}|{name} ({cc})|{theme[:30]}|{liner[:60]}|{(sum_v1 or sum_en)[:70]}")
