import sqlite3

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

# Manual mapping of clusters to themes (based on cluster labels from output)
CLUSTER_THEME_MAP = {
    0: 'Biomaterials & Green Chemistry',      # Materials
    1: 'Precision Agriculture',                # Agronomic
    2: 'Diagnostics & Devices',               # Diagnostics
    3: 'Nature & Ecosystem Tech',             # Satellite
    4: 'Nature & Ecosystem Tech',             # Carbon
    5: 'Diagnostics & Devices',               # Skin
    6: 'Therapeutics',                        # Biosimilar
    7: 'Bioinputs & Crop Resilience',        # Crop Resilience
    8: None,                                  # Ecuador - Mixed, need further investigation
    9: 'Biomaterials & Green Chemistry',      # Drug Delivery
    10: 'Food Systems & Alt Proteins',        # Anid (bioinputs but in food cluster)
    11: 'Therapeutics',                       # Regenerative Medicine
    12: 'Therapeutics',                       # Drug Discovery
    13: 'Food Systems & Alt Proteins',        # Functional Ingredients
    14: 'Digital AgTech & Agrifintech',       # Precision Fermentation
    15: 'Food Systems & Alt Proteins',        # Aquaculture
    16: 'Food Systems & Alt Proteins',        # Dairy
    17: 'Food Systems & Alt Proteins',        # Food Waste
    18: 'Food Systems & Alt Proteins',        # Microalgae
}

print("MAPPING CLUSTERS TO THEMES AND ASSIGNING BIO_THEME TO 61 STARTUPS\n")

# Get the 61 startups without bio_theme in clusters
c.execute('''
SELECT startup_id, cluster_id
FROM startup_extended
WHERE cluster_id >= 0 AND (bio_theme_primary IS NULL OR bio_theme_primary = "")
ORDER BY cluster_id, startup_id
''')

uncategorized = c.fetchall()
print(f"Found {len(uncategorized)} startups without bio_theme\n")

# Group by cluster
by_cluster = {}
for startup_id, cluster_id in uncategorized:
    if cluster_id not in by_cluster:
        by_cluster[cluster_id] = []
    by_cluster[cluster_id].append(startup_id)

# Show mapping and prepare enrichments
enrichments = []
assigned = 0
unassigned = 0

for cluster_id in sorted(by_cluster.keys()):
    theme = CLUSTER_THEME_MAP.get(cluster_id)
    startups = by_cluster[cluster_id]

    status = "ASSIGNED" if theme else "UNASSIGNED"
    print(f"Cluster {cluster_id}: {len(startups)} startups -> {theme or 'Unknown'} [{status}]")

    for startup_id in startups:
        if theme:
            enrichments.append({
                'entity_id': startup_id,
                'table_name': 'startup_extended',
                'field_name': 'bio_theme_primary',
                'new_value': theme,
                'source_url': 'https://research.biolatam.io/clustering-inference',
                'confidence': 0.7,
                'notes': f'Inferred from cluster {cluster_id} theme mapping'
            })
            assigned += 1
        else:
            unassigned += 1

print(f"\n=== RESULT ===")
print(f"Assigned: {assigned}/61")
print(f"Unassigned: {unassigned}/61")

# Save enrichments
import csv
out_path = 'staging/entity_enrichments.csv'
with open(out_path, 'w', newline='', encoding='utf-8') as f:
    if enrichments:
        writer = csv.DictWriter(f, fieldnames=enrichments[0].keys())
        writer.writeheader()
        for e in enrichments:
            writer.writerow(e)

print(f"\nSaved {len(enrichments)} enrichments to: {out_path}")
print(f"Ready to ingest: python pipeline.py ingest-entity-enrichments")

conn.close()
