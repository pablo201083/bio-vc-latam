import sqlite3
from collections import Counter

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

# Get the 364 unclustered
c.execute('''
SELECT startup_id, business_one_liner
FROM startup_extended
WHERE cluster_id = -1 AND review_status != 'EXCLUDE'
ORDER BY startup_id
''')

unclustered = c.fetchall()

print("=" * 80)
print("364 UNCLUSTERED STARTUPS - DISTRIBUTION BY COUNTRY")
print("=" * 80)
print(f"\nTotal: {len(unclustered)}\n")

# Extract countries
countries = Counter()
by_country = {}

for sid, desc in unclustered:
    # Extract country code (last 2 chars after last hyphen)
    parts = sid.split('-')
    if len(parts) >= 2:
        country_code = parts[-1].upper()
        countries[country_code] += 1

        if country_code not in by_country:
            by_country[country_code] = []
        by_country[country_code].append({
            'id': sid,
            'desc': desc[:60] if desc else '(no description)'
        })

# Show distribution
print("DISTRIBUTION:\n")
for country, count in countries.most_common():
    pct = 100 * count // len(unclustered)
    print(f"{country}: {count:3d} startups ({pct:2d}%)")

# Show top countries with samples
print(f"\n" + "=" * 80)
print("TOP COUNTRIES - SAMPLE STARTUPS")
print("=" * 80)

for country, count in countries.most_common(5):
    print(f"\n{country} ({count} startups):")
    samples = by_country[country][:5]
    for item in samples:
        print(f"  - {item['id']}")
        print(f"    {item['desc']}...")

print(f"\n" + "=" * 80)
print("RESEARCH STRATEGY")
print("=" * 80)
print(f"""
Total research effort: 364 startups * 5-10 min = 30-60 hours

RECOMMENDED BATCH STRATEGY:
1. BR (87): Brazil - largest batch, most documented market
2. CO (37): Colombia - 2nd largest
3. MX (29): Mexico - 3rd largest
4. CL (25): Chile - 4th largest
5. PE (20): Peru - 5th largest
   Subtotal: 198 startups (54% of total)

6. Remaining 15 countries: 166 startups (46%)

Each batch can be researched in parallel using agents.
""")

conn.close()
