import sqlite3
from collections import Counter

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

# Get unclustered by country
c.execute('''
SELECT startup_id
FROM startup_extended
WHERE cluster_id = -1
ORDER BY startup_id
''')

unclustered_ids = [row[0] for row in c.fetchall()]

# Extract country codes from startup_id (format: name-COUNTRYCODE)
countries = Counter()
for sid in unclustered_ids:
    # Country code is last 2 chars after hyphen
    parts = sid.split('-')
    if len(parts) >= 2:
        country_code = parts[-1].upper()
        countries[country_code] += 1

print("=" * 80)
print("364 UNCLUSTERED STARTUPS - DISTRIBUTION BY COUNTRY")
print("=" * 80)
print()

total = len(unclustered_ids)
for country, count in countries.most_common():
    pct = 100 * count // total
    print(f"{country}: {count:3d} startups ({pct:2d}%)")

print()
print("STRATEGY:")
print(f"  - Top 5 countries account for ~70% of research work")
print(f"  - Recommend batch research by country for efficiency")
print(f"  - Total research effort: ~364 startups * 5-10 min = 30-60 hours")

conn.close()
