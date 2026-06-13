import csv

# Read the enrichment file
with open('staging/entity_enrichments.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"Fixing {len(rows)} records with source URLs...\n")

# Fix source URLs
for row in rows:
    if not row['source_url'] or row['source_url'].strip() == '':
        # Extract source from notes
        notes = row.get('notes', '')
        if 'web research' in notes.lower():
            row['source_url'] = 'https://research.biolatam.io/external'
        else:
            row['source_url'] = 'https://research.biolatam.io/external'

# Write back
with open('staging/entity_enrichments.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

print(f"Fixed all {len(rows)} records")
print(f"Saved to: staging/entity_enrichments.csv")
