import sqlite3
import csv

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

print("=" * 80)
print("EXCLUDING 340 NON-BIOTECH + EXTRACTING 24 BIOTECH CANDIDATES")
print("=" * 80)

# Biotech keywords
BIOTECH_KEYWORDS = [
    'bio', 'biotech', 'biopharm', 'pharmaceutical', 'drug', 'gene', 'cell', 'therapeutic',
    'diagnostic', 'medtech', 'health', 'clinical', 'vaccine', 'antibody', 'protein',
    'agri', 'agro', 'crop', 'farm', 'plant', 'seed', 'food', 'cultivated',
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

# Separate biotech from non-biotech
biotech_candidates = []
non_biotech_ids = []

for sid, desc in unclustered:
    desc_lower = (desc or '').lower()
    has_biotech = any(kw in desc_lower for kw in BIOTECH_KEYWORDS)

    if has_biotech:
        biotech_candidates.append((sid, desc))
    else:
        non_biotech_ids.append(sid)

print(f"\nEXCLUDING {len(non_biotech_ids)} NON-BIOTECH...\n")

# Mark non-biotech as EXCLUDE
for sid in non_biotech_ids:
    c.execute("UPDATE startup_extended SET review_status = 'EXCLUDE' WHERE startup_id = ?", (sid,))

conn.commit()
print(f"Marked {len(non_biotech_ids)} as EXCLUDE")

# Export biotech candidates for research
out_path = 'staging/research_24_biotech_candidates.csv'
with open(out_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['startup_id', 'current_description', 'research_priority'])

    for sid, desc in biotech_candidates:
        priority = 'CRITICAL' if not desc or len(desc) < 20 else 'HIGH'
        writer.writerow([sid, desc[:100] if desc else '(empty)', priority])

print(f"\nEXTRACTED {len(biotech_candidates)} BIOTECH CANDIDATES")
print(f"Exported to: {out_path}\n")

# Show the 24
print("=" * 80)
print("THE 24 BIOTECH CANDIDATES")
print("=" * 80 + "\n")

for i, (sid, desc) in enumerate(biotech_candidates, 1):
    print(f"{i:2d}. {sid}")
    if desc:
        print(f"    {desc[:70]}...")
    else:
        print(f"    (no description)")

# Verify
c.execute("SELECT COUNT(*) FROM startup_extended WHERE cluster_id = -1 AND review_status != 'EXCLUDE'")
remaining = c.fetchone()[0]

print(f"\n\nRemaining unclustered (active): {remaining}")

conn.close()
