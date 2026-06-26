"""Audit data quality distribution — find the bottom."""
import sqlite3, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
conn = sqlite3.connect(ROOT / "db" / "bio_latam.db")

print("=== DISTRIBUCIÓN DE CALIDAD (include) ===\n")

# Quality bands
bands = conn.execute("""
    SELECT quality_band, COUNT(*) as n
    FROM startup_extended WHERE scope_decision='include'
    GROUP BY quality_band ORDER BY n DESC
""").fetchall()
print("Quality bands:")
for band, n in bands:
    bar = "#" * (n // 5)
    print(f"  {str(band):<20} {n:>4}  {bar}")

# Key field coverage
fields = [
    ("startup_summary_en", "startup_extended", "LENGTH(startup_summary_en) >= 80"),
    ("bio_theme_confidence > 0", "startup_extended", "bio_theme_confidence > 0"),
    ("bio_theme_confidence IS NULL", "startup_extended", "bio_theme_confidence IS NULL OR bio_theme_confidence = 0"),
    ("trl_current_status", "startup_extended", "trl_current_status IS NOT NULL AND trl_current_status != ''"),
    ("tech_depth", "startup_extended", "tech_depth IS NOT NULL AND tech_depth != ''"),
    ("tech_codes", "startup_extended", "tech_codes IS NOT NULL AND tech_codes != ''"),
    ("founded_year", "entities", "founded_year IS NOT NULL"),
    ("source externa auditable", "startup_extended", "scope_basis = 'external_auditable_source'"),
    ("missing_signals vacío", "startup_extended", "missing_signals IS NULL OR missing_signals = ''"),
    ("valuation_tier", "startup_extended", "valuation_tier IS NOT NULL AND valuation_tier != ''"),
]

print("\nCobertura de campos clave:")
total = conn.execute("SELECT COUNT(*) FROM startup_extended WHERE scope_decision='include'").fetchone()[0]
for label, table, condition in fields:
    if table == "entities":
        n = conn.execute(f"""
            SELECT COUNT(*) FROM entities e
            JOIN startup_extended sx ON sx.startup_id = e.entity_id
            WHERE sx.scope_decision='include' AND e.{condition}
        """).fetchone()[0]
    else:
        n = conn.execute(f"""
            SELECT COUNT(*) FROM startup_extended
            WHERE scope_decision='include' AND {condition}
        """).fetchone()[0]
    pct = n * 100 // total
    bar = "#" * (pct // 5)
    print(f"  {label:<35} {n:>4}/{total}  {pct:>3}%  {bar}")

# Bottom 20 by computed_quality_score
print("\n=== BOTTOM 20 por computed_quality_score ===")
bottom = conn.execute("""
    SELECT sx.startup_id, e.canonical_name, e.country_code,
           sx.computed_quality_score, sx.quality_band,
           sx.scope_basis, sx.bio_theme_confidence,
           sx.bio_theme_primary, sx.trl_current_status,
           sx.tech_depth
    FROM startup_extended sx
    JOIN entities e ON e.entity_id = sx.startup_id
    WHERE sx.scope_decision = 'include'
    ORDER BY sx.computed_quality_score ASC NULLS FIRST
    LIMIT 20
""").fetchall()

print(f"{'ID':<40} {'Name':<28} {'CC':<4} {'Score':<7} {'Band':<12} {'Basis':<25} {'ThConf':<7} {'TRL':<6} {'TechD'}")
print("-"*160)
for row in bottom:
    sid, name, cc, score, band, basis, thconf, bio_theme, trl, techd = row
    print(f"{str(sid):<40} {str(name)[:26]:<28} {str(cc):<4} {str(score)[:5]:<7} {str(band)[:10]:<12} {str(basis)[:23]:<25} {str(thconf)[:5]:<7} {str(trl)[:5]:<6} {str(techd)[:10]}")

conn.close()
