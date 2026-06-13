import sqlite3

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

print("=" * 80)
print("DATABASE GAPS AUDIT - Critical fields for clustering & labeling")
print("=" * 80)

# Key fields for quality clustering
CRITICAL_FIELDS = [
    ('startup_extended', 'business_one_liner', 'Description (business_one_liner)'),
    ('startup_extended', 'startup_summary_en', 'Summary (startup_summary_en)'),
    ('startup_extended', 'tech_codes', 'Tech codes'),
    ('startup_extended', 'industry_codes', 'Industry codes'),
    ('startup_extended', 'bio_theme_primary', 'Bio theme (primary)'),
]

print("\nCRITICAL FIELD COMPLETENESS:\n")

for table, field, label in CRITICAL_FIELDS:
    c.execute(f'SELECT COUNT(*) FROM {table} WHERE {field} IS NULL OR {field} = ""')
    nulls = c.fetchone()[0]
    c.execute(f'SELECT COUNT(*) FROM {table}')
    total = c.fetchone()[0]
    pct = 100 * (total - nulls) / total if total > 0 else 0

    status = "OK" if pct > 90 else "WARN" if pct > 50 else "FAIL"
    print(f"[{status}] {label:40} {pct:5.1f}% complete ({total - nulls}/{total})")

# Focus on the 61 uncategorized in Mixed clusters
print("\n\nFOCUS: UNCATEGORIZED IN MIXED CLUSTERS (0, 1)\n")

c.execute('''
SELECT cluster_id, COUNT(*) as cnt,
       SUM(CASE WHEN business_one_liner IS NULL OR business_one_liner = "" THEN 1 ELSE 0 END) as null_desc,
       SUM(CASE WHEN startup_summary_en IS NULL OR startup_summary_en = "" THEN 1 ELSE 0 END) as null_summary
FROM startup_extended
WHERE cluster_id IN (0, 1)
GROUP BY cluster_id
''')

for cluster_id, cnt, null_desc, null_summary in c.fetchall():
    print(f"Cluster {cluster_id}: {cnt} startups")
    print(f"  Missing business_one_liner: {null_desc}/{cnt}")
    print(f"  Missing startup_summary_en: {null_summary}/{cnt}")

# Check what data IS available for these startups
print("\n\nAVAILABLE DATA FOR MIXED STARTUPS:\n")

c.execute('''
SELECT
    COUNT(*) as total,
    SUM(CASE WHEN tech_codes IS NOT NULL AND tech_codes != "" THEN 1 ELSE 0 END) as has_tech,
    SUM(CASE WHEN industry_codes IS NOT NULL AND industry_codes != "" THEN 1 ELSE 0 END) as has_industry
FROM startup_extended
WHERE cluster_id IN (0, 1)
''')

total, has_tech, has_industry = c.fetchone()
print(f"Total in Mixed clusters: {total}")
print(f"With tech_codes: {has_tech or 0}")
print(f"With industry_codes: {has_industry or 0}")

# Check alternate sources in other tables
print("\n\nALTERNATE DATA SOURCES:\n")

# Check if founders/investors exist
c.execute('''
SELECT COUNT(DISTINCT se.startup_id)
FROM startup_extended se
WHERE se.cluster_id IN (0, 1)
AND EXISTS (SELECT 1 FROM founder_edges fe WHERE fe.startup_id = se.startup_id)
''')
with_founders = c.fetchone()[0]
print(f"With founder data (from founder_edges): {with_founders}")

c.execute('''
SELECT COUNT(DISTINCT se.startup_id)
FROM startup_extended se
WHERE se.cluster_id IN (0, 1)
AND EXISTS (SELECT 1 FROM investment_edges ie WHERE ie.startup_id = se.startup_id)
''')
with_investors = c.fetchone()[0]
print(f"With investor data (from investment_edges): {with_investors}")

conn.close()

print("\n" + "=" * 80)
print("RECOMMENDATION: Fill business_one_liner for Mixed startups from:")
print("  1. tech_codes + industry_codes synthesis")
print("  2. Founder/investor context")
print("  3. Then re-cluster with complete data")
print("=" * 80)
