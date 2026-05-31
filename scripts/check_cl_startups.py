"""List Chilean startups without CORFO edges"""
import sqlite3

conn = sqlite3.connect("db/bio_latam.db")

print("=== Chilean startups without CORFO support edge ===")
rows = conn.execute("""
    SELECT se.startup_id, e.canonical_name, e.website, se.data_quality_score, se.bio_theme_primary
    FROM startup_extended se
    JOIN entities e ON se.startup_id = e.entity_id
    WHERE e.country_code = 'CL'
      AND se.is_bio_universe = 1
      AND se.data_quality_score >= 6.0
    ORDER BY se.data_quality_score DESC
""").fetchall()

for r in rows:
    startup_id, name, website, score, theme = r
    has_corfo = conn.execute(
        "SELECT COUNT(*) FROM support_edges WHERE source_entity_id='corfo' AND target_entity_id=?",
        (startup_id,)
    ).fetchone()[0]
    marker = "[CORFO]" if has_corfo else ""
    print(f"  {startup_id:<35} | {name:<28} | Q:{score:.1f} | {marker} | {website or ''}")

print(f"\nTotal CL startups (quality >= 6): {len(rows)}")
