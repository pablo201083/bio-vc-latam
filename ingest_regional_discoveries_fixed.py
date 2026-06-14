"""
Ingiere startups regionales descubiertas + sus inversores
Versión corregida: unicode fixes + investor names correctas
"""

import sqlite3
import csv
from difflib import SequenceMatcher

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

print("=" * 80)
print("INGESTING REGIONAL DISCOVERIES - PHASE 2 (EDGES ONLY)")
print("=" * 80)

# Las startups ya fueron ingrestas. Ahora solo agregamos edges.
# Startups descubiertas que ya existen en BD + sus inversores

edges_to_ingest = [
    # Peru startups descubiertas + inversores
    ('soillab-peru-pe', 'salkantay_ventures', 0.85),
    ('nutritech-andina-pe', 'carao_ventures', 0.80),
    ('phage-solutions-peru-pe', 'idb_lab', 0.85),
    ('bioamazonia-pe', 'idb_lab', 0.85),
    ('aquavida-biotech-pe', 'the_yield_lab_latam', 0.80),

    # Nuevas startups Peru que se ingresaron
    ('tilapia-innovations-pe', 'salkantay_ventures', 0.80),
    ('terrabiology-peru-pe', 'carao_ventures', 0.80),
    ('perugrow-biotech-pe', 'the_yield_lab_latam', 0.80),

    # Ecuador
    ('aquaecuador-ec', 'carao_ventures', 0.80),
    ('biodiversidad-ecuador-ec', 'idb_lab', 0.80),

    # Dominican Republic
    ('agro360-do', 'idb_lab', 0.85),
    ('agricultic-do', 'idb_lab', 0.80),
]

print(f"\nProcessing {len(edges_to_ingest)} edges...")

ingested = 0
skipped = 0
errors = 0

for startup_id, investor_id, confidence in edges_to_ingest:
    try:
        # Verificar que startup existe
        c.execute('SELECT startup_id FROM startup_extended WHERE startup_id = ?', (startup_id,))
        if not c.fetchone():
            print(f"  [SKIP] {startup_id:35} (startup not found in DB)")
            skipped += 1
            continue

        # Verificar que investor existe
        c.execute('SELECT investor_id FROM investors WHERE investor_id = ?', (investor_id,))
        if not c.fetchone():
            print(f"  [SKIP] {investor_id:30} (investor not found)")
            skipped += 1
            continue

        # Crear edge
        investment_id = f'REGIONAL_{investor_id}_{startup_id}'
        c.execute('''
        INSERT OR IGNORE INTO investment_edges (
            investment_id, investor_id, startup_id, round_name, round_stage,
            announced_date, amount, currency, is_lead, confidence_score,
            source_id, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            investment_id,
            investor_id,
            startup_id,
            'portfolio',
            None,
            None,
            None,
            None,
            0,
            confidence,
            'REGIONAL_DISCOVERY',
            f'Regional research: {investor_id}'
        ))

        if c.rowcount > 0:
            print(f"  [OK] {investor_id:30} -> {startup_id:35} ({confidence:.2f})")
            ingested += 1
        else:
            print(f"  [DUP] {investor_id:30} -> {startup_id:35} (already exists)")
            skipped += 1

    except Exception as e:
        print(f"  [ERROR] {startup_id}: {str(e)[:60]}")
        errors += 1

conn.commit()

print(f"\nResults:")
print(f"  Ingested: {ingested}")
print(f"  Skipped: {skipped}")
print(f"  Errors: {errors}")

# Estado final
c.execute('SELECT COUNT(*) FROM startup_extended WHERE cluster_id >= 0')
total_bio = c.fetchone()[0]

c.execute('''
SELECT COUNT(DISTINCT startup_id) FROM investment_edges
WHERE startup_id IN (SELECT startup_id FROM startup_extended WHERE cluster_id >= 0)
''')
with_edges = c.fetchone()[0]

c.execute('SELECT COUNT(*) FROM investment_edges')
total_edges = c.fetchone()[0]

print(f"\nFINAL STATE:")
print(f"  BIO startups: {total_bio}")
print(f"  With investors: {with_edges}/{total_bio} ({100*with_edges//total_bio}%)")
print(f"  Total edges: {total_edges}")

# Regional coverage
print(f"\nRegional Coverage:")
for cc in ['PE', 'EC', 'DO', 'VE', 'GT', 'PA', 'BO']:
    c.execute('''
    SELECT COUNT(DISTINCT ie.startup_id), COUNT(DISTINCT ie.investor_id)
    FROM investment_edges ie
    WHERE ie.startup_id IN (
      SELECT startup_id FROM startup_extended
      WHERE startup_id LIKE ? AND cluster_id >= 0
    )
    ''', (f'%-{cc}',))

    startups, investors = c.fetchone()
    print(f"  {cc}: {startups} startups with {investors} investors")

conn.close()
print("\n[DONE]")
