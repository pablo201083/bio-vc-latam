import sqlite3

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

print("=" * 80)
print("COBERTURA ACTUAL - CHECKUP COMPLETO")
print("=" * 80)

# 1. TOTAL STARTUPS
c.execute('SELECT COUNT(*) FROM startup_extended')
total = c.fetchone()[0]
print(f"\nTOTAL STARTUPS EN BD: {total}")

# 2. UNIVERSE BREAKDOWN (included/exclude/review)
c.execute('''
SELECT
  SUM(CASE WHEN review_status = 'INCLUDE' THEN 1 ELSE 0 END) as included,
  SUM(CASE WHEN review_status = 'EXCLUDE' THEN 1 ELSE 0 END) as excluded,
  SUM(CASE WHEN review_status = 'REVIEW' THEN 1 ELSE 0 END) as review
FROM startup_extended
''')
included, excluded, review = c.fetchone()
print(f"\nUNIVERSO:")
print(f"  INCLUDE (core biotech): {included}")
print(f"  EXCLUDE (out of scope): {excluded}")
print(f"  REVIEW (uncertain): {review}")

# 3. CLUSTERING COVERAGE
c.execute('SELECT COUNT(*) FROM startup_extended WHERE cluster_id >= 0')
clustered = c.fetchone()[0]
unclustered = total - clustered
print(f"\nCLUSTERING:")
print(f"  Clustered (cluster_id >= 0): {clustered} ({100*clustered//total}%)")
print(f"  Unclustered (cluster_id = -1): {unclustered} ({100*unclustered//total}%)")

# 4. BIO_THEME COMPLETENESS
c.execute('SELECT COUNT(*) FROM startup_extended WHERE cluster_id >= 0 AND (bio_theme_primary IS NOT NULL AND bio_theme_primary != "")')
with_theme = c.fetchone()[0]
without_theme = clustered - with_theme
print(f"\nBIO_THEME (within clustered):")
print(f"  With bio_theme_primary: {with_theme} ({100*with_theme//clustered}%)")
print(f"  Without bio_theme_primary: {without_theme} ({100*without_theme//clustered}%)")

# 5. DESCRIPTIONS
c.execute('SELECT COUNT(*) FROM startup_extended WHERE business_one_liner IS NOT NULL AND business_one_liner != ""')
with_desc = c.fetchone()[0]
print(f"\nDESCRIPCIONES:")
print(f"  business_one_liner: {with_desc}/{total} ({100*with_desc//total}%)")

# 6. TECH CODES
c.execute('SELECT COUNT(*) FROM startup_extended WHERE tech_codes IS NOT NULL AND tech_codes != ""')
with_tech = c.fetchone()[0]
print(f"  tech_codes: {with_tech}/{total} ({100*with_tech//total}%)")

# 7. THEME DISTRIBUTION
print(f"\nDISTRIBUCION DE TEMAS (top 8):")
c.execute('''
SELECT bio_theme_primary, COUNT(*) as cnt
FROM startup_extended
WHERE bio_theme_primary IS NOT NULL AND bio_theme_primary != ""
GROUP BY bio_theme_primary
ORDER BY cnt DESC
LIMIT 8
''')
for theme, cnt in c.fetchall():
    pct = 100 * cnt // clustered
    print(f"  {theme}: {cnt} ({pct}%)")

# 8. CLUSTERS
c.execute('SELECT COUNT(DISTINCT cluster_id) FROM startup_extended WHERE cluster_id >= 0')
num_clusters = c.fetchone()[0]
print(f"\nCLUSTERS SEMANTICOS: {num_clusters}")

# 9. QUALITY SUMMARY
print(f"\n" + "=" * 80)
print("RESUMEN DE CALIDAD")
print("=" * 80)

quality_score = (100 * with_theme // clustered) + (100 * with_desc // total) + (100 * with_tech // total)
quality_score = quality_score // 3

print(f"\nCOBERTURA GENERAL: {quality_score}%")

if quality_score >= 95:
    status = "EXCELENTE"
    symbol = "OK"
elif quality_score >= 85:
    status = "BUENA"
    symbol = "OK"
elif quality_score >= 70:
    status = "ACEPTABLE"
    symbol = "WARN"
else:
    status = "NECESITA MEJORA"
    symbol = "FAIL"

print(f"STATUS: [{symbol}] {status}\n")

# 10. GAPS IDENTIFICADOS
print("GAPS IDENTIFICADOS:")
if without_theme > 0:
    print(f"  - {without_theme} startups sin bio_theme en clusters")
if (total - with_desc) > 0:
    print(f"  - {total - with_desc} startups sin descripción")
if (total - with_tech) > 0:
    print(f"  - {total - with_tech} startups sin tech_codes")

print()
conn.close()
