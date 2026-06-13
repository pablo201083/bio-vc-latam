import sqlite3

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

# Get the 46 high priority
c.execute('''
SELECT
  se.startup_id,
  se.business_one_liner,
  COUNT(DISTINCT ie.investor_id) as investor_count
FROM startup_extended se
LEFT JOIN investment_edges ie ON ie.startup_id = se.startup_id
WHERE se.cluster_id = -1
  AND se.business_one_liner IS NOT NULL
  AND se.business_one_liner != ""
GROUP BY se.startup_id, se.business_one_liner
HAVING COUNT(DISTINCT ie.investor_id) > 0
ORDER BY COUNT(DISTINCT ie.investor_id) DESC, se.startup_id
''')

all_46 = c.fetchall()

# Biotech keywords to filter
BIOTECH_KEYWORDS = [
    'bio', 'biotech', 'biomedical', 'therapeutics', 'pharmaceutical',
    'agri', 'agro', 'crop', 'farm', 'plant', 'agriculture',
    'food', 'protein', 'cultivated', 'ferment',
    'diagnos', 'medtech', 'med tech', 'health tech',
    'genetic', 'gene therapy', 'cell', 'dna',
    'material', 'biomaterial', 'biodegradable',
    'enzyme', 'microb', 'bacteria', 'organism',
    'vaccine', 'immunotherapy', 'antibody',
    'lab', 'laboratory', 'research', 'development',
    'clinical', 'therapy', 'treatment', 'cure',
    'diagnostic', 'test', 'detection'
]

NON_BIOTECH_KEYWORDS = [
    'software', 'platform', 'app', 'application', 'saas',
    'crypto', 'blockchain', 'wallet', 'finance', 'banking',
    'logistics', 'freight', 'shipping', 'supply chain',
    'education', 'edtech', 'learning',
    'recruiting', 'recruitment', 'hr', 'human resources',
    'space', 'communications', 'electronics',
    'construction', 'real estate', 'property'
]

biotech_startups = []
non_biotech_startups = []

for sid, desc, inv_count in all_46:
    desc_lower = desc.lower() if desc else ''

    # Check for biotech signals
    is_biotech = any(kw in desc_lower for kw in BIOTECH_KEYWORDS)
    is_non_biotech = any(kw in desc_lower for kw in NON_BIOTECH_KEYWORDS)

    if is_biotech and not is_non_biotech:
        biotech_startups.append((sid, desc, inv_count))
    else:
        non_biotech_startups.append((sid, desc, inv_count))

print("=" * 80)
print("FILTERING: BIOTECH vs NON-BIOTECH FROM 46 HIGH PRIORITY")
print("=" * 80)
print(f"\nBIOTECH (likely valid): {len(biotech_startups)}")
print(f"NON-BIOTECH (misclassified): {len(non_biotech_startups)}")
print(f"\nBREAKDOWN:\n")

if biotech_startups:
    print("BIOTECH STARTUPS FOR RESEARCH:")
    for i, (sid, desc, inv_count) in enumerate(biotech_startups[:15], 1):
        print(f"  {i}. {sid} ({inv_count} investors)")
        print(f"     {desc[:60]}...")
else:
    print("(No biotech startups found in high priority list)")

if non_biotech_startups:
    print(f"\nNON-BIOTECH (should be EXCLUDED from BIO ecosystem):")
    for i, (sid, desc, inv_count) in enumerate(non_biotech_startups[:10], 1):
        print(f"  {i}. {sid} ({inv_count} investors)")
        print(f"     {desc[:60]}...")

print(f"\nRECOMMENDATION:")
print(f"  - Research {len(biotech_startups)} biotech startups")
print(f"  - Flag {len(non_biotech_startups)} for removal (non-biotech)")

conn.close()
