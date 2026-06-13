import sqlite3
import csv

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

# Get the 29 unclustered (not EXCLUDE)
c.execute('''
SELECT startup_id, business_one_liner
FROM startup_extended
WHERE cluster_id = -1 AND review_status != 'EXCLUDE'
ORDER BY startup_id
''')

unclustered = c.fetchall()

print("=" * 80)
print("29 UNCLUSTERED BIOTECH STARTUPS - FOR WEB RESEARCH")
print("=" * 80)
print(f"\nTotal: {len(unclustered)}\n")

# Extract country distribution
from collections import Counter
countries = Counter()

for sid, desc in unclustered:
    parts = sid.split('-')
    if len(parts) >= 2:
        country = parts[-1].upper()
        countries[country] += 1

print("DISTRIBUTION BY COUNTRY:\n")
for country, count in countries.most_common():
    print(f"{country}: {count}")

# List all 29
print(f"\n" + "=" * 80)
print("THE 29 STARTUPS")
print("=" * 80 + "\n")

for i, (sid, desc) in enumerate(unclustered, 1):
    print(f"{i:2d}. {sid}")
    if desc:
        print(f"    {desc[:70]}...")
    else:
        print(f"    (no description)")

# Export for research
out_path = 'staging/research_29_unclustered.csv'
with open(out_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['startup_id', 'current_description', 'research_priority'])

    for sid, desc in unclustered:
        priority = 'CRITICAL' if not desc else 'HIGH'
        writer.writerow([sid, desc[:100] if desc else '(empty)', priority])

print(f"\n\nResearch template exported: {out_path}")

conn.close()
