"""Find top AR/BR biotech startups to cross-reference with public funding"""
import sqlite3

conn = sqlite3.connect("db/bio_latam.db")

print("=== High-quality AR startups (potential ANPCYT targets) ===")
rows = conn.execute("""
    SELECT se.startup_id, e.canonical_name, e.website,
           se.data_quality_score, se.bio_theme_primary, se.funding_stage
    FROM startup_extended se
    JOIN entities e ON se.startup_id = e.entity_id
    WHERE e.country_code = 'AR'
      AND se.data_quality_score >= 7.0
      AND se.is_bio_universe = 1
    ORDER BY se.data_quality_score DESC
    LIMIT 30
""").fetchall()

for r in rows:
    startup_id, name, website, score, theme, stage = r
    has_anpcyt = conn.execute(
        "SELECT COUNT(*) FROM support_edges WHERE source_entity_id='anpcyt' AND target_entity_id=?",
        (startup_id,)
    ).fetchone()[0]
    if not has_anpcyt:
        print(f"  {startup_id:<35} | {name:<28} | Q:{score:.1f} | {website or ''}")

print("\n=== High-quality BR startups (potential FINEP/SEBRAE targets) ===")
rows = conn.execute("""
    SELECT se.startup_id, e.canonical_name, e.website,
           se.data_quality_score, se.bio_theme_primary
    FROM startup_extended se
    JOIN entities e ON se.startup_id = e.entity_id
    WHERE e.country_code = 'BR'
      AND se.data_quality_score >= 7.0
      AND se.is_bio_universe = 1
    ORDER BY se.data_quality_score DESC
    LIMIT 20
""").fetchall()

for r in rows:
    startup_id, name, website, score, theme = r
    has_finep = conn.execute(
        "SELECT COUNT(*) FROM support_edges WHERE source_entity_id='finep' AND target_entity_id=?",
        (startup_id,)
    ).fetchone()[0]
    if not has_finep:
        print(f"  {startup_id:<35} | {name:<28} | Q:{score:.1f} | {website or ''}")
