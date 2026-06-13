import sqlite3
import csv

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

print("=" * 80)
print("FINALIZING BIO SUBSPACE - EXCLUDE 14 NON-BIOTECH")
print("=" * 80)

# The 14 NO-biotech from research
no_biotech_14 = [
    'agroadvance', 'audsat', 'bacu', 'beyond_renewable_energy',
    'brasil_ozonio', 'flexza', 'inti_tech', 'partanna',
    'popai', 'reborn_electric_motors', 'starlight_ventures',
    'verge_ag', 'vixtra', 'yak'
]

print(f"\nEXCLUDING {len(no_biotech_14)} NON-BIOTECH CANDIDATES...\n")

# Mark as EXCLUDE
for sid in no_biotech_14:
    c.execute("UPDATE startup_extended SET review_status = 'EXCLUDE' WHERE startup_id = ?", (sid,))
    print(f"  {sid}")

conn.commit()
print(f"\nMarked {len(no_biotech_14)} as EXCLUDE")

# Prepare enrichment for Aguamarina (the 1 core biotech)
aguamarina_enrichments = [
    {
        'entity_id': 'aguamarina_biomineria',
        'table_name': 'startup_extended',
        'field_name': 'business_one_liner',
        'new_value': 'Uses bio-lixiviation with bacteria and microalgae from seawater to recover minerals sustainably from mining waste',
        'source_url': 'https://research.biolatam.io/web-research-24',
        'confidence': 0.95,
        'notes': 'Core biotech R&D - authentic biotech innovation'
    },
    {
        'entity_id': 'aguamarina_biomineria',
        'table_name': 'startup_extended',
        'field_name': 'tech_codes',
        'new_value': 'bio_lixiviation_bacteria_microalgae_minerals_recovery',
        'source_url': 'https://research.biolatam.io/web-research-24',
        'confidence': 0.9,
        'notes': 'Bio-based mining technology'
    },
    {
        'entity_id': 'aguamarina_biomineria',
        'table_name': 'startup_extended',
        'field_name': 'industry_codes',
        'new_value': 'biomineria_sustainable_mining_bioinputs',
        'source_url': 'https://research.biolatam.io/web-research-24',
        'confidence': 0.9,
        'notes': 'Biotech-enabled mining innovation'
    }
]

# Save enrichments
out_path = 'staging/entity_enrichments.csv'
with open(out_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['entity_id', 'table_name', 'field_name', 'new_value', 'source_url', 'confidence', 'notes'])
    writer.writeheader()
    for e in aguamarina_enrichments:
        writer.writerow(e)

print(f"\nCreated enrichments for Aguamarina")
print(f"Saved to: {out_path}")

# Verify final state
c.execute("SELECT COUNT(*) FROM startup_extended WHERE review_status = 'EXCLUDE'")
total_exclude = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM startup_extended WHERE cluster_id = -1 AND review_status != 'EXCLUDE'")
remaining = c.fetchone()[0]

print(f"\nFINAL STATE:")
print(f"  Total EXCLUDE: {total_exclude}")
print(f"  Remaining unclustered (active): {remaining}")

# Show the pure BIO subspace stats
c.execute('''
SELECT
  COUNT(*) as total,
  SUM(CASE WHEN cluster_id >= 0 THEN 1 ELSE 0 END) as clustered,
  SUM(CASE WHEN cluster_id >= 0 AND (bio_theme_primary IS NOT NULL AND bio_theme_primary != "") THEN 1 ELSE 0 END) as with_theme
FROM startup_extended
WHERE review_status != 'EXCLUDE'
''')

total_active, clustered, with_theme = c.fetchone()

print(f"\nPURE BIO SUBSPACE (review_status != 'EXCLUDE'):")
print(f"  Total: {total_active}")
print(f"  Clustered: {clustered} ({100*clustered//total_active if total_active else 0}%)")
print(f"  With bio_theme: {with_theme} ({100*with_theme//total_active if total_active else 0}%)")

conn.close()

print(f"\n" + "=" * 80)
print("READY FOR FINAL CLUSTERING")
print("=" * 80)
