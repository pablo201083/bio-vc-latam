import sqlite3
from collections import Counter

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

print("=" * 80)
print("FILTERING 364 UNCLUSTERED - BIOTECH CANDIDATES ONLY")
print("=" * 80)

# Comprehensive biotech keywords
BIOTECH_KEYWORDS = [
    'bio', 'biotech', 'biopharm', 'pharmaceutical', 'drug', 'gene', 'cell', 'therapeutic',
    'diagnostic', 'medtech', 'health', 'clinical', 'vaccine', 'antibody', 'protein',
    'agri', 'agro', 'crop', 'farm', 'plant', 'seed', 'food', 'protein', 'cultivated',
    'material', 'biomaterial', 'biodegradable', 'polymer', 'enzyme', 'microbe',
    'genetic', 'dna', 'rna', 'genome', 'ferment', 'bioprocess',
    'ecosystem', 'environmental', 'carbon', 'sustainability', 'nature', 'restoration'
]

# Get ALL unclustered
c.execute('''
SELECT startup_id, business_one_liner
FROM startup_extended
WHERE cluster_id = -1
ORDER BY startup_id
''')

unclustered = c.fetchall()

print(f"\nTotal unclustered: {len(unclustered)}\n")

# Filter by biotech keywords
biotech_candidates = []
non_biotech = []

for sid, desc in unclustered:
    desc_lower = (desc or '').lower()

    # Check for biotech signals
    has_biotech = any(kw in desc_lower for kw in BIOTECH_KEYWORDS)

    if has_biotech:
        biotech_candidates.append((sid, desc))
    else:
        non_biotech.append(sid)

print(f"RESULTS:")
print(f"  BIOTECH CANDIDATES: {len(biotech_candidates)}")
print(f"  CLEAR NON-BIOTECH: {len(non_biotech)}")

# Show distribution of candidates by country
countries = Counter()
for sid, desc in biotech_candidates:
    parts = sid.split('-')
    if len(parts) >= 2:
        country = parts[-1].upper()
        countries[country] += 1

print(f"\nBIOTECH CANDIDATES BY COUNTRY:\n")
for country, count in countries.most_common(10):
    print(f"  {country}: {count}")

print(f"\n" + "=" * 80)
print("STRATEGY")
print("=" * 80)
print(f"""
BIOTECH candidates to research: {len(biotech_candidates)}
NON-BIOTECH to exclude: {len(non_biotech)}

This reduces research scope from 364 to {len(biotech_candidates)} (~{100*len(biotech_candidates)//len(unclustered)}%).
Estimated research time: {len(biotech_candidates)*5//60}-{len(biotech_candidates)*10//60} hours

NEXT STEPS:
1. Exclude {len(non_biotech)} non-biotech immediately
2. Research {len(biotech_candidates)} biotech candidates
3. Clusterizar el subespacio BIO puro
""")

conn.close()
