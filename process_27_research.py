import sqlite3
import csv

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

print("=" * 80)
print("PROCESSING 27 RESEARCH RESULTS")
print("=" * 80)

# Read the research results CSV
research_data = {}
with open('staging/research_27_unclustered_final.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        startup_id = row.get('startup_id', '').strip()
        biotech_signal = row.get('biotech_signal', '').strip().upper()
        if startup_id:
            research_data[startup_id] = {
                'biotech': biotech_signal,
                'description': row.get('description', ''),
                'tech_focus': row.get('tech_focus', ''),
                'industry': row.get('industry_sector', ''),
                'confidence': row.get('confidence', '0.5')
            }

print(f"\nResearch data loaded: {len(research_data)} records\n")

# Separate biotech from non-biotech
biotech_9 = []
non_biotech_13 = []

for sid, data in research_data.items():
    signal = data['biotech']
    if signal == 'YES':
        biotech_9.append((sid, data))
    else:
        non_biotech_13.append((sid, data))

print(f"BIOTECH (YES): {len(biotech_9)}")
print(f"NON-BIOTECH (NO/QUESTIONABLE): {len(non_biotech_13)}\n")

# Create enrichments for biotech startups
enrichments = []

for sid, data in biotech_9:
    # Add description
    if data['description']:
        enrichments.append({
            'entity_id': sid,
            'table_name': 'startup_extended',
            'field_name': 'business_one_liner',
            'new_value': data['description'][:150],
            'source_url': 'https://research.biolatam.io/web-research-27',
            'confidence': float(data['confidence']),
            'notes': f'Web research - {data["industry"]}'
        })

    # Add tech_focus as tech_codes
    if data['tech_focus']:
        enrichments.append({
            'entity_id': sid,
            'table_name': 'startup_extended',
            'field_name': 'tech_codes',
            'new_value': data['tech_focus'].replace(' ', '_').replace('/', '_').lower(),
            'source_url': 'https://research.biolatam.io/web-research-27',
            'confidence': max(0.5, float(data['confidence']) - 0.1),
            'notes': f'Tech keywords from web research'
        })

    # Add industry_codes
    if data['industry']:
        enrichments.append({
            'entity_id': sid,
            'table_name': 'startup_extended',
            'field_name': 'industry_codes',
            'new_value': data['industry'].replace(' ', '_').replace('&', 'and').lower(),
            'source_url': 'https://research.biolatam.io/web-research-27',
            'confidence': max(0.5, float(data['confidence']) - 0.1),
            'notes': f'Industry from web research'
        })

# Save enrichments
out_path = 'staging/entity_enrichments.csv'
with open(out_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['entity_id', 'table_name', 'field_name', 'new_value', 'source_url', 'confidence', 'notes'])
    writer.writeheader()
    for e in enrichments:
        writer.writerow(e)

print(f"Created {len(enrichments)} enrichment records")
print(f"Saved to: {out_path}\n")

# Prepare exclusion list for non-biotech
exclusion_list = []
for sid, data in non_biotech_13:
    exclusion_list.append(sid)

print(f"Non-biotech to exclude: {len(exclusion_list)}")
print(f"IDs: {exclusion_list}\n")

# Mark non-biotech as EXCLUDE in DB
for sid in exclusion_list:
    c.execute("UPDATE startup_extended SET review_status = 'EXCLUDE' WHERE startup_id = ?", (sid,))

conn.commit()

print(f"Updated DB: {len(exclusion_list)} marked as EXCLUDE")

# Verify
c.execute("SELECT COUNT(*) FROM startup_extended WHERE cluster_id = -1 AND review_status != 'EXCLUDE'")
remaining = c.fetchone()[0]

print(f"\nRemaining unclustered (not EXCLUDE): {remaining}")

conn.close()

print(f"\n" + "=" * 80)
print("NEXT: Ingest enrichments + re-cluster")
print("=" * 80)
