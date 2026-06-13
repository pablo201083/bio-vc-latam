import sqlite3

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

# Get the 7 uncategorized in cluster 8
c.execute('''
SELECT
  startup_id,
  cluster_id,
  cluster_label,
  business_one_liner,
  startup_summary_en,
  tech_codes,
  industry_codes
FROM startup_extended
WHERE cluster_id = 8 AND (bio_theme_primary IS NULL OR bio_theme_primary = "")
ORDER BY startup_id
''')

startups = c.fetchall()
print(f"=" * 80)
print(f"7 UNCATEGORIZED STARTUPS IN CLUSTER 8 (ECUADOR REGION)")
print(f"=" * 80)
print(f"\nCluster label: Ecuador/Lab/Democratizes/CNPQ\n")

for i, (sid, cid, clabel, desc, summary, tech, industry) in enumerate(startups, 1):
    print(f"{i}. {sid}")
    print(f"   Description: {desc[:80] if desc else '(none)'}...")
    print(f"   Summary: {summary[:80] if summary else '(none)'}...")
    print(f"   Tech codes: {tech if tech else '(none)'}")
    print(f"   Industry: {industry if industry else '(none)'}")
    print()

# Create CSV for research
import csv
out_path = 'staging/research_7_ecuador.csv'
with open(out_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['startup_id', 'current_description', 'research_priority'])
    for sid, cid, clabel, desc, summary, tech, industry in startups:
        writer.writerow([sid, desc or summary or '(no data)', 'HIGH'])

print(f"Research template saved: {out_path}")
conn.close()
