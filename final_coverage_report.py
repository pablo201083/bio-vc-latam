import sqlite3

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

print("=" * 80)
print("COBERTURA DE DATOS - REPORTE FINAL")
print("=" * 80)

# Total universe
c.execute('SELECT COUNT(*) FROM startup_extended')
total = c.fetchone()[0]

c.execute('''
SELECT
  SUM(CASE WHEN review_status = 'INCLUDE' THEN 1 ELSE 0 END) as included,
  SUM(CASE WHEN review_status = 'EXCLUDE' THEN 1 ELSE 0 END) as excluded,
  SUM(CASE WHEN review_status = 'REVIEW' THEN 1 ELSE 0 END) as review,
  SUM(CASE WHEN review_status IN ('seeded', 'pending', 'reviewed') OR review_status IS NULL THEN 1 ELSE 0 END) as other
FROM startup_extended
''')
included, excluded, review, other = c.fetchone()

print(f"\n1. UNIVERSO TOTAL: {total} startups")
print(f"   INCLUDE (core biotech): {included}")
print(f"   EXCLUDE (out of scope): {excluded} ({100*excluded//total}%)")
print(f"   REVIEW (uncertain): {review}")
print(f"   OTHER (seeded/pending/reviewed/null): {other}")

# Clustering
c.execute('SELECT COUNT(*) FROM startup_extended WHERE cluster_id >= 0')
clustered = c.fetchone()[0]
unclustered = total - clustered

print(f"\n2. CLUSTERING: {clustered}/{total} ({100*clustered//total}%)")
print(f"   Clustered: {clustered}")
print(f"   Unclustered: {unclustered} ({100*unclustered//total}%)")

# Bio_theme in clustered
c.execute('SELECT COUNT(*) FROM startup_extended WHERE cluster_id >= 0 AND (bio_theme_primary IS NOT NULL AND bio_theme_primary != "")')
with_theme = c.fetchone()[0]
without_theme = clustered - with_theme

print(f"\n3. BIO_THEME (en clustered): {with_theme}/{clustered} ({100*with_theme//clustered}%)")
print(f"   Con tema: {with_theme}")
print(f"   Sin tema: {without_theme}")

# Descriptions
c.execute('SELECT COUNT(*) FROM startup_extended WHERE business_one_liner IS NOT NULL AND business_one_liner != ""')
with_desc = c.fetchone()[0]

print(f"\n4. DESCRIPCIONES: {with_desc}/{total} ({100*with_desc//total}%)")
print(f"   business_one_liner: {with_desc}")
print(f"   Faltan: {total - with_desc}")

# Tech codes
c.execute('SELECT COUNT(*) FROM startup_extended WHERE tech_codes IS NOT NULL AND tech_codes != ""')
with_tech = c.fetchone()[0]

print(f"\n5. TECH_CODES: {with_tech}/{total} ({100*with_tech//total}%)")
print(f"   Con tech_codes: {with_tech}")
print(f"   Faltan: {total - with_tech}")

# Industry codes
c.execute('SELECT COUNT(*) FROM startup_extended WHERE industry_codes IS NOT NULL AND industry_codes != ""')
with_industry = c.fetchone()[0]

print(f"\n6. INDUSTRY_CODES: {with_industry}/{total} ({100*with_industry//total}%)")
print(f"   Con industry_codes: {with_industry}")
print(f"   Faltan: {total - with_industry}")

# Quality score
c.execute('SELECT COUNT(*) FROM startup_extended WHERE computed_quality_score IS NOT NULL AND computed_quality_score > 0')
with_quality = c.fetchone()[0]

print(f"\n7. QUALITY_SCORE: {with_quality}/{total} ({100*with_quality//total}%)")
print(f"   Con score: {with_quality}")
print(f"   Faltan: {total - with_quality}")

# Funding stage
c.execute('SELECT COUNT(*) FROM startup_extended WHERE funding_stage IS NOT NULL AND funding_stage != ""')
with_funding = c.fetchone()[0]

print(f"\n8. FUNDING_STAGE: {with_funding}/{total} ({100*with_funding//total}%)")
print(f"   Con stage: {with_funding}")
print(f"   Faltan: {total - with_funding}")

# Summary score
print(f"\n" + "=" * 80)
print("RESUMEN DE COBERTURA")
print("=" * 80)

overall = (100*clustered//total + 100*with_theme//total + 100*with_desc//total + 100*with_tech//total) // 4

print(f"\nCOBERTURA PROMEDIO: {overall}%")

# Breakdown
print(f"\nDETALLE:")
print(f"  Clustering:     {100*clustered//total}%")
print(f"  Bio_theme:      {100*with_theme//total}%")
print(f"  Descripciones:  {100*with_desc//total}%")
print(f"  Tech_codes:     {100*with_tech//total}%")
print(f"  Funding:        {100*with_funding//total}%")

# Major gaps
print(f"\nGAPS PRINCIPALES:")
print(f"  - {unclustered} unclustered (necesitan research/clustering)")
print(f"  - {total - with_desc} sin descripción")
print(f"  - {total - with_tech} sin tech_codes")
print(f"  - {total - with_funding} sin funding_stage")

# Bio-theme distribution
print(f"\n" + "=" * 80)
print("DISTRIBUCION DE TEMAS (en clustered)")
print("=" * 80 + "\n")

c.execute('''
SELECT bio_theme_primary, COUNT(*) as cnt
FROM startup_extended
WHERE cluster_id >= 0 AND bio_theme_primary IS NOT NULL AND bio_theme_primary != ""
GROUP BY bio_theme_primary
ORDER BY cnt DESC
''')

for theme, cnt in c.fetchall():
    pct = 100 * cnt // clustered
    print(f"{theme:40} {cnt:3d} ({pct:2d}%)")

conn.close()
