"""Load high-risk startups with their website URLs for inline summary writing."""
import csv, pathlib, sqlite3

ROOT = pathlib.Path(__file__).resolve().parent.parent
conn = sqlite3.connect(ROOT / "db" / "bio_latam.db")

rows = conn.execute("""
    SELECT sx.startup_id, e.canonical_name, e.country_code,
           e.website,
           coalesce(sx.startup_summary_en, '') as summary_en,
           coalesce(sx.startup_summary_v1, '') as summary_v1,
           coalesce(sx.business_one_liner, '') as one_liner,
           coalesce(sx.macro_theme, sx.bio_theme_primary, '') as theme,
           coalesce(sx.cluster_confidence, 0) as conf
    FROM startup_extended sx
    JOIN entities e ON e.entity_id = sx.startup_id
    WHERE sx.scope_decision = 'include'
      AND (sx.startup_summary_en IS NULL OR length(sx.startup_summary_en) < 100)
    ORDER BY sx.cluster_confidence ASC
    LIMIT 40
""").fetchall()
conn.close()

for sid, name, cc, url, sum_en, sum_v1, liner, theme, conf in rows:
    has_url = "YES" if url and url.startswith("http") else "NO"
    print(f"{sid}|{name}|{cc}|{has_url}|{url or ''}|{theme}|{liner[:60]}|{(sum_v1 or sum_en)[:80]}")
