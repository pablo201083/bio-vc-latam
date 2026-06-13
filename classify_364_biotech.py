import sqlite3
import csv

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

print("=" * 80)
print("CLASSIFYING 364 UNCLUSTERED BY BIOTECH RELEVANCE")
print("=" * 80)

# Comprehensive biotech keywords
BIOTECH_KEYWORDS = [
    # Core biotech
    'bio', 'biotech', 'biopharm', 'bioscience',
    # Therapeutics
    'therapeutic', 'therapeutics', 'pharmaceutical', 'pharma', 'drug', 'vaccine',
    'gene therapy', 'cell therapy', 'immunotherapy', 'antibody',
    # Agriculture/Food
    'agri', 'agro', 'agrotech', 'agriculture', 'agricultural',
    'crop', 'crops', 'farm', 'farming', 'farmer',
    'plant', 'plants', 'seed', 'seeds', 'fertilizer',
    'food', 'protein', 'cultivated', 'fermented', 'ferment',
    'biologics', 'bioinput', 'biopesticide',
    # Medical/Health
    'diagnos', 'diagnostic', 'medtech', 'med tech', 'medical',
    'health', 'healthcare', 'biomedical', 'clinical',
    # Materials/Chemistry
    'material', 'biomaterial', 'biopolymer', 'biodegradable',
    'green chemistry', 'green chemistry',
    # Biology/Science
    'genetic', 'genetics', 'genome', 'genomic', 'dna', 'rna',
    'cell', 'cells', 'cellular', 'enzyme', 'protein', 'proteins',
    'microbe', 'bacteria', 'microbiology',
    # Sustainability/Environment
    'sustainability', 'sustainable', 'environmental', 'environment',
    'climate', 'carbon', 'ecosystem',
    # Platform/Tech
    'bioprocess', 'fermentation', 'biofactory', 'cdmo', 'platform'
]

# Get all 364 unclustered
c.execute('''
SELECT startup_id, business_one_liner
FROM startup_extended
WHERE cluster_id = -1
ORDER BY startup_id
''')

unclustered = c.fetchall()
print(f"\nTotal: {len(unclustered)}\n")

# Classify each
biotech_ids = []
non_biotech_ids = []
unclassified_ids = []

for sid, desc in unclustered:
    desc_lower = (desc or '').lower()

    if desc_lower.strip() == '':
        # No description
        unclassified_ids.append((sid, 'UNCLASSIFIED', 'No description'))
    else:
        # Check for biotech signals
        is_biotech = any(kw in desc_lower for kw in BIOTECH_KEYWORDS)

        if is_biotech:
            biotech_ids.append((sid, desc))
        else:
            non_biotech_ids.append((sid, desc))

print(f"CLASSIFICATION RESULTS:\n")
print(f"BIOTECH (keywords match): {len(biotech_ids)}")
print(f"NON-BIOTECH (no match): {len(non_biotech_ids)}")
print(f"UNCLASSIFIED (no description): {len(unclassified_ids)}")
print(f"TOTAL: {len(unclustered)}")

# Show samples
print(f"\n" + "=" * 80)
print("SAMPLES - BIOTECH (to keep)")
print("=" * 80)
for i, (sid, desc) in enumerate(biotech_ids[:15], 1):
    print(f"{i}. {sid}")
    print(f"   {desc[:70]}...")

print(f"\n" + "=" * 80)
print("SAMPLES - NON-BIOTECH (to exclude)")
print("=" * 80)
for i, (sid, desc) in enumerate(non_biotech_ids[:15], 1):
    print(f"{i}. {sid}")
    print(f"   {desc[:70]}...")

# Create exclusion list for DB update
print(f"\n" + "=" * 80)
print("CREATING EXCLUSION LIST")
print("=" * 80)

out_path = 'staging/exclude_non_biotech.csv'
with open(out_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['startup_id', 'current_status', 'new_status', 'reason'])

    for sid, desc in non_biotech_ids:
        writer.writerow([sid, 'REVIEW', 'EXCLUDE', 'Non-biotech (tech/fintech/other sector)'])

    for sid, _, reason in unclassified_ids:
        writer.writerow([sid, 'REVIEW', 'EXCLUDE', reason])

print(f"\nExclusion list saved: {out_path}")
print(f"Total to exclude: {len(non_biotech_ids) + len(unclassified_ids)}")
print(f"Total to keep (BIOTECH): {len(biotech_ids)}")

# Create research list for biotech
out_path2 = 'staging/research_biotech_classified.csv'
with open(out_path2, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['startup_id', 'description', 'priority'])

    for sid, desc in biotech_ids:
        priority = 'CRITICAL' if not desc or desc.strip() == '' else 'HIGH'
        writer.writerow([sid, desc[:100] if desc else '(empty)', priority])

print(f"Biotech research list saved: {out_path2}")

print(f"\n" + "=" * 80)
print(f"NEXT STEPS:")
print(f"=" * 80)
print(f"1. Update DB: mark {len(non_biotech_ids) + len(unclassified_ids)} as EXCLUDE")
print(f"2. Research {len(biotech_ids)} BIOTECH startups")
print(f"3. Re-cluster with cleaned data")

conn.close()
