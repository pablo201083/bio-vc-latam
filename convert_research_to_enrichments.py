import csv

# Read research results
with open('staging/research_results_61_mixed.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"Converting {len(rows)} research records to entity enrichments...\n")

# Create enrichment records for ingestion
enrichments = []

for row in rows:
    startup_id = row['startup_id']
    description = row['description']
    tech_focus = row['tech_focus']
    industry = row['industry_sector']
    confidence = float(row['confidence'])

    # Only add records with some data (confidence > 0.1)
    if confidence > 0.1 and description and description != 'Unknown':
        # Add description
        enrichments.append({
            'entity_id': startup_id,
            'table_name': 'startup_extended',
            'field_name': 'business_one_liner',
            'new_value': description[:150],  # Truncate to 150 chars
            'source_url': '',
            'confidence': confidence,
            'notes': f'From web research - {row["source_found"]}'
        })

    # Add tech_codes if available
    if confidence > 0.2 and tech_focus and tech_focus != 'Unknown':
        enrichments.append({
            'entity_id': startup_id,
            'table_name': 'startup_extended',
            'field_name': 'tech_codes',
            'new_value': tech_focus.replace(' ', '_').replace('-', '_').lower(),
            'source_url': '',
            'confidence': max(0.5, confidence - 0.1),
            'notes': f'Tech keywords from web research'
        })

# Save as CSV for ingestion
out_path = 'staging/enrichments_61_mixed_research.csv'
with open(out_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['entity_id', 'table_name', 'field_name', 'new_value', 'source_url', 'confidence', 'notes'])
    writer.writeheader()
    for e in enrichments:
        writer.writerow(e)

print(f"Converted {len(enrichments)} enrichment records")
print(f"Saved to: {out_path}")
print(f"\nNext: python pipeline.py ingest-entity-enrichments --file {out_path}")
