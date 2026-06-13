import sqlite3
import csv

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

print("SYNTHESIZING DESCRIPTIONS FROM TECH + INDUSTRY CODES\n")

# Get the 61 Mixed startups with their codes
c.execute('''
SELECT startup_id, cluster_id, tech_codes, industry_codes
FROM startup_extended
WHERE cluster_id IN (0, 1)
ORDER BY startup_id
''')

startups = c.fetchall()
print(f"Processing {len(startups)} startups...\n")

# Create entity enrichments for BD ingestion
enrichments = []
for startup_id, cluster_id, tech_codes, industry_codes in startups:
    # Synthesize description from codes
    techs = tech_codes.split('|') if tech_codes else []
    industries = industry_codes.split('|') if industry_codes else []

    # Take first 2-3 from each
    top_techs = [t.strip() for t in techs[:2] if t.strip()]
    top_industries = [i.strip() for i in industries[:2] if i.strip()]

    # Build description
    parts = []
    if top_techs:
        parts.append(' + '.join(top_techs))
    if top_industries:
        parts.append('for ' + ' + '.join(top_industries))

    description = ' '.join(parts).strip() if parts else 'Bio-tech solution'

    # Add capitalization
    if description:
        description = description[0].upper() + description[1:]

    enrichments.append({
        'entity_id': startup_id,
        'table_name': 'startup_extended',
        'field_name': 'business_one_liner',
        'new_value': description,
        'source_url': '',
        'confidence': 0.8,
        'notes': f'Synthesized from tech_codes + industry_codes'
    })

    print(f"{startup_id}: {description[:60]}")

# Save as CSV for ingestion
csv_path = 'staging/synthesized_descriptions_61.csv'
with open(csv_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['entity_id', 'table_name', 'field_name', 'new_value', 'source_url', 'confidence', 'notes'])
    writer.writeheader()
    for e in enrichments:
        writer.writerow(e)

print(f"\nSaved: {csv_path}")
print(f"Next: ingest these descriptions, then re-cluster")

conn.close()
