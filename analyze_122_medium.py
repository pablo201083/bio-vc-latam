import sqlite3

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

# Get 122 MEDIUM PRIORITY (desc only, no investors)
c.execute('''
SELECT
  se.startup_id,
  se.business_one_liner
FROM startup_extended se
WHERE se.cluster_id = -1
  AND se.business_one_liner IS NOT NULL
  AND se.business_one_liner != ""
  AND NOT EXISTS (SELECT 1 FROM investment_edges ie WHERE ie.startup_id = se.startup_id)
ORDER BY se.startup_id
''')

medium_priority = c.fetchall()

print(f"=" * 80)
print(f"ANALYZING 122 MEDIUM PRIORITY (description only, no investors)")
print(f"=" * 80)
print(f"\nTotal: {len(medium_priority)}\n")

# Biotech keywords
BIOTECH_KEYWORDS = [
    'bio', 'biotech', 'therapeutic', 'pharmaceutical',
    'agri', 'agro', 'crop', 'farm', 'plant',
    'food', 'protein', 'cultivated',
    'diagnos', 'medtech', 'health',
    'genetic', 'cell', 'vaccine',
    'material', 'biomaterial'
]

biotech_count = 0
non_biotech_count = 0

biotech_samples = []
non_biotech_samples = []

for sid, desc in medium_priority:
    desc_lower = desc.lower() if desc else ''
    is_biotech = any(kw in desc_lower for kw in BIOTECH_KEYWORDS)

    if is_biotech:
        biotech_count += 1
        if len(biotech_samples) < 10:
            biotech_samples.append((sid, desc))
    else:
        non_biotech_count += 1
        if len(non_biotech_samples) < 10:
            non_biotech_samples.append((sid, desc))

print(f"BIOTECH (keywords match): {biotech_count} ({100*biotech_count//len(medium_priority)}%)")
print(f"NON-BIOTECH: {non_biotech_count} ({100*non_biotech_count//len(medium_priority)}%)")

if biotech_samples:
    print(f"\nBIOTECH SAMPLES:")
    for sid, desc in biotech_samples:
        print(f"  - {sid}")
        print(f"    {desc[:70]}...")

if non_biotech_samples:
    print(f"\nNON-BIOTECH SAMPLES:")
    for sid, desc in non_biotech_samples:
        print(f"  - {sid}")
        print(f"    {desc[:70]}...")

print(f"\n" + "=" * 80)
print(f"ASSESSMENT:")
print(f"=" * 80)
print(f"\nOf 364 unclustered:")
print(f"  - 46 HIGH (investors): 0 biotech, 46 non-biotech")
print(f"  - 122 MEDIUM (desc): ~{biotech_count} biotech, ~{non_biotech_count} non-biotech")
print(f"  - 195 PHANTOM (no data): unknown")
print(f"\nRecommendation: Clean dataset first, remove non-biotech entries")

conn.close()
