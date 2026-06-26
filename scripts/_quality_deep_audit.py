"""Deep audit: what drives computed_quality_score and what's missing."""
import sqlite3, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
conn = sqlite3.connect(ROOT / "db" / "bio_latam.db")

# TRL distribution
print("=== TRL coverage ===")
trl_dist = conn.execute("""
    SELECT trl_current_status, COUNT(*) as n
    FROM startup_extended WHERE scope_decision='include'
    GROUP BY trl_current_status ORDER BY n DESC
""").fetchall()
for trl, n in trl_dist:
    print(f"  {str(trl):<20} {n}")

# bio_theme_confidence distribution
print("\n=== bio_theme_confidence distribution ===")
conf_dist = conn.execute("""
    SELECT
        CASE
            WHEN bio_theme_confidence IS NULL THEN 'NULL'
            WHEN bio_theme_confidence = 0 THEN '0.0'
            WHEN bio_theme_confidence < 0.5 THEN '<0.5'
            WHEN bio_theme_confidence < 0.7 THEN '0.5-0.7'
            WHEN bio_theme_confidence < 0.9 THEN '0.7-0.9'
            ELSE '>=0.9'
        END as bucket,
        COUNT(*) as n
    FROM startup_extended WHERE scope_decision='include'
    GROUP BY bucket ORDER BY n DESC
""").fetchall()
for bucket, n in conf_dist:
    print(f"  {bucket:<12} {n}")

# Breakdown: auto_discovery vs external with no confidence
print("\n=== Sin bio_theme_confidence por scope_basis ===")
no_conf = conn.execute("""
    SELECT scope_basis, COUNT(*) as n
    FROM startup_extended
    WHERE scope_decision='include'
      AND (bio_theme_confidence IS NULL OR bio_theme_confidence = 0)
    GROUP BY scope_basis ORDER BY n DESC
""").fetchall()
for basis, n in no_conf:
    print(f"  {str(basis):<30} {n}")

# Startups with external source but no TRL (easy wins)
print("\n=== External source + NO TRL (easy wins) ===")
easy = conn.execute("""
    SELECT sx.startup_id, e.canonical_name, e.country_code,
           sx.bio_theme_primary, sx.tech_depth, sx.startup_summary_en
    FROM startup_extended sx
    JOIN entities e ON e.entity_id = sx.startup_id
    WHERE sx.scope_decision='include'
      AND sx.scope_basis = 'external_auditable_source'
      AND (sx.trl_current_status IS NULL OR sx.trl_current_status = '')
    ORDER BY e.canonical_name
    LIMIT 30
""").fetchall()
total_easy = conn.execute("SELECT COUNT(*) FROM startup_extended WHERE scope_decision='include' AND scope_basis='external_auditable_source' AND (trl_current_status IS NULL OR trl_current_status='')").fetchone()[0]
print(f"Total external+no_TRL: {total_easy}")
for sid, name, cc, theme, depth, summary in easy:
    s = (summary or "")[:60]
    print(f"  {sid:<38} {str(cc):<4} depth={str(depth):<10} {s}")

conn.close()
