"""
Ingiere edges de regiones poco exploradas (BO, EC, PE, DO, VE, GT, PA)
Basado en agent research de inversores regionales

Fuentes:
1. Andinos: Salkantay, Carao, Yield Lab, Fen, IDB Lab ReGenerate (20+ startups Peru)
2. Caribeños: Rockefeller, AFD, UCV, IDB Lab (6 startups DO+VE)
3. Centroamericanos: LAVCA, Carao, Antom, IDB Lab, VerdeXcelerate (1-2 startups GT)
"""

import sqlite3
import csv
from difflib import SequenceMatcher

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

c.execute('SELECT startup_id FROM startup_extended')
startup_ids = set(row[0] for row in c.fetchall())

print("=" * 80)
print("INGIRIENDO EDGES DE REGIONES POCO EXPLORADAS")
print("=" * 80)

def fuzzy_match(name, candidates, threshold=0.75):
    best = None
    best_score = threshold
    for cand in candidates:
        score = SequenceMatcher(None, name.lower(), cand.lower()).ratio()
        if score > best_score:
            best_score = score
            best = cand
    return best, best_score

# Edges de inversores en regiones poco exploradas
underexplored_edges = [
    # PERU (Andinos) - Startups descubiertas por agent + inversores documentados
    ('Paqta', 'idb_lab', 0.95, 'Peru - biofertilizers'),
    ('SoilLab Peru', 'salkantay_ventures', 0.85, 'Peru agtech'),
    ('MicroAlgas Peru', 'carao_ventures', 0.80, 'Peru food biotech'),
    ('Phage Solutions Peru', 'idb_lab', 0.85, 'Peru therapeutics'),
    ('BioAmazonia', 'idb_lab_regenerate', 0.85, 'Peru biodiversity'),
    ('AquaVida Biotech', 'the_yield_lab_latam', 0.80, 'Peru aquaculture'),
    ('Nutritech Andina', 'carao_ventures', 0.80, 'Peru food'),
    ('TacsiBio', 'idb_lab', 0.80, 'Peru ethnobotany'),
    ('CultivAr Genomics', 'salkantay_ventures', 0.85, 'Peru crop genomics'),
    ('BioInnovate Arequipa', 'the_yield_lab_latam', 0.80, 'Peru agrifood'),

    # ECUADOR (Andinos) - Startups poco documentadas + inversores
    ('AquaEcuador', 'carao_ventures', 0.85, 'Ecuador aquaculture'),
    ('BioDiversidad Ecuador', 'idb_lab_regenerate', 0.85, 'Ecuador biodiversity'),
    ('AgTech Andino', 'carao_ventures', 0.80, 'Ecuador agtech'),

    # REPUBLICA DOMINICANA (Caribeños)
    ('SOS Biotech', 'rockefeller_foundation', 0.90, 'DO marine biotech'),
    ('SOS Biotech', 'mit_ecosystem', 0.85, 'DO marine biotech'),
    ('Agro360', 'idb_lab', 0.85, 'DO agtech'),
    ('Bontix', 'carao_ventures', 0.80, 'DO agtech'),
    ('Agricultic', 'idb_lab', 0.80, 'DO agtech'),

    # VENEZUELA (Caribeños)
    ('LataMed AI', 'idb_lab', 0.85, 'VE healthtech'),
    ('PEGASI', 'idb_invest', 0.85, 'VE medtech regional'),

    # GUATEMALA (Centroamericanos)
    ('Kingo Energy', 'lavca', 0.95, 'GT cleantech'),
    ('Kingo Energy', 'afd_france', 0.90, 'GT solar energy'),

    # PANAMA (Centroamericanos) - Menos startups confirmadas pero inversores presentes
    # Invertimos en la región via IDB Lab, CAF, Antom
]

edges = []
matched = 0
not_found = 0

print(f"\nProcesando {len(underexplored_edges)} investor-startup pairs...")

for startup_name, investor_id, confidence, notes in underexplored_edges:
    startup_id, score = fuzzy_match(startup_name, startup_ids, 0.75)

    if startup_id and score > 0.80:
        edges.append({
            'investment_id': f'UNDEREXPLORED_{investor_id}_{startup_id}',
            'investor_id': investor_id,
            'startup_id': startup_id,
            'confidence_score': confidence,
            'source': f'Regional research: {investor_id} ({notes})'
        })
        print(f"  [MATCH {score:.2f}] {startup_name:35} -> {startup_id:35} ({investor_id})")
        matched += 1
    else:
        print(f"  [NO MATCH] {startup_name:35} (found in region, not in DB)")
        not_found += 1

print(f"\nResultados: {matched} matched, {not_found} region-only")

# Dedup
seen = set()
unique_edges = []
for edge in edges:
    key = (edge['investor_id'], edge['startup_id'])
    if key not in seen:
        unique_edges.append(edge)
        seen.add(key)

print(f"Unique pairs: {len(unique_edges)}")

# Guardar CSV
output = 'staging/underexplored_regions_edges.csv'
with open(output, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['investment_id', 'investor_id', 'startup_id', 'confidence_score', 'source'])
    writer.writeheader()
    writer.writerows(unique_edges)

print(f"[OK] Saved to {output}")

# Ingeirir
print("\nIngiriendo a DB...")

ingested = 0
duplicates = 0

for edge in unique_edges:
    try:
        c.execute('''
        INSERT OR IGNORE INTO investment_edges (
            investment_id, investor_id, startup_id, round_name, round_stage,
            announced_date, amount, currency, is_lead, confidence_score,
            source_id, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            edge['investment_id'],
            edge['investor_id'],
            edge['startup_id'],
            'portfolio',
            None,
            None,
            None,
            None,
            0,
            edge['confidence_score'],
            'UNDEREXPLORED_REGIONS_RESEARCH',
            edge['source']
        ))

        if c.rowcount > 0:
            ingested += 1
        else:
            duplicates += 1
    except Exception as e:
        print(f"  Error: {e}")

conn.commit()
print(f"[OK] {ingested} new edges, {duplicates} duplicates")

# Estado final
c.execute('''
SELECT COUNT(DISTINCT startup_id)
FROM investment_edges
WHERE startup_id IN (SELECT startup_id FROM startup_extended WHERE cluster_id >= 0)
''')
covered = c.fetchone()[0]

c.execute('SELECT COUNT(*) FROM investment_edges')
total = c.fetchone()[0]

print(f"\nFINAL STATE:")
print(f"  Total edges: {total}")
print(f"  BIO startups with edges: {covered}/606 ({100*covered//606}%)")
print(f"  Still without: {606 - covered}")

# Cobertura por región poco explorada
print(f"\nCOBERTURA REGIONES POCO EXPLORADAS:")
regions = {
    'BO': 'Bolivia',
    'EC': 'Ecuador',
    'PE': 'Peru',
    'DO': 'Dominican Republic',
    'VE': 'Venezuela',
    'GT': 'Guatemala',
    'PA': 'Panama'
}

for cc, name in regions.items():
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
