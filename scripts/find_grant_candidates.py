"""
Find top Argentine/Brazilian startups to cross-reference with ANPCYT/FINEP grants.
Priority: high quality score + biotech vertical + AR/BR country.
"""
import sqlite3
sys.stdout.reconfigure if False else None

conn = sqlite3.connect("db/bio_latam.db")

print("=== High-quality AR startups (potential ANPCYT targets) ===")
for r in conn.execute("""
    SELECT se.startup_id, e.canonical_name, e.website,
           se.data_quality_score, se.bio_theme_primary, se.funding_stage
    FROM startup_extended se
    JOIN entities e ON se.startup_id = e.entity_id
    WHERE e.country_code = 'AR'
      AND se.data_quality_score >= 7.0
      AND se.is_bio_universe = 1
    ORDER BY se.data_quality_score DESC
    LIMIT 30
"""):
    startup_id, name, website, score, theme, stage = r
    # Check if already has ANPCYT edge
    has_anpcyt = conn.execute(
        "SELECT COUNT(*) FROM support_edges WHERE source_entity_id='anpcyt' AND target_entity_id=?",
        (startup_id,)
    ).fetchone()[0]
    if not has_anpcyt:
        print(f"  {startup_id:35s} | {name:30s} | {theme:35s} | Q:{score} | {website or 'no-web'}")

print("\n=== High-quality BR startups (potential FINEP/SEBRAE targets) ===")
for r in conn.execute("""
    SELECT se.startup_id, e.canonical_name, e.website,
           se.data_quality_score, se.bio_theme_primary, se.funding_stage
    FROM startup_extended se
    JOIN entities e ON se.startup_id = e.entity_id
    WHERE e.country_code = 'BR'
      AND se.data_quality_score >= 7.0
      AND se.is_bio_universe = 1
    ORDER BY se.data_quality_score DESC
    LIMIT 20
"""):
    startup_id, name, website, score, theme, stage = r
    has_finep = conn.execute(
        "SELECT COUNT(*) FROM support_edges WHERE source_entity_id='finep' AND target_entity_id=?",
        (startup_id,)
    ).fetchone()[0]
    has_sebrae = conn.execute(
        "SELECT COUNT(*) FROM support_edges WHERE source_entity_id='sebrae' AND target_entity_id=?",
        (startup_id,)
    ).fetchone()[0]
    if not has_finep and not has_sebrae:
        print(f"  {startup_id:35s} | {name:30s} | {theme:35s} | Q:{score} | {website or 'no-web'}")
