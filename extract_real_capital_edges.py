"""
Extrae datos reales de inversión de fuentes:
1. investment_edges_raw.csv (edgeseco.csv - ya validado)
2. accelerator_portfolio_biotech_latam_2024-2025.csv
3. vc_biotech_portfolio_latam.csv

Mapea a startup_id/investor_id reales usando fuzzy matching.
"""

import sqlite3
import csv
from difflib import SequenceMatcher

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

print("=" * 80)
print("EXTRAYENDO DATOS REALES DE CAPITAL")
print("=" * 80)

# Cargar mapa de canonical entity IDs
c.execute('SELECT startup_id FROM startup_extended')
startup_ids = set(row[0] for row in c.fetchall())

c.execute('SELECT investor_id FROM investors')
investor_ids = set(row[0] for row in c.fetchall())

print(f"\n1. Mapa de entidades:")
print(f"   Startups en DB: {len(startup_ids)}")
print(f"   Inversores en DB: {len(investor_ids)}")

# Función fuzzy match
def find_match(name, candidates, threshold=0.6):
    """Busca mejor match por similaridad de strings"""
    best_match = None
    best_score = threshold

    for candidate in candidates:
        score = SequenceMatcher(None, name.lower(), candidate.lower()).ratio()
        if score > best_score:
            best_score = score
            best_match = candidate

    return best_match, best_score

# 2. Procesar investment_edges_raw.csv
print(f"\n2. Procesando investment_edges_raw.csv...")

real_edges = []
matched = 0
unmatched_investors = set()
unmatched_startups = set()

with open('staging/investment_edges_raw.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)

    for row in reader:
        investor_name = row['investor_id_candidate'].strip()
        startup_name = row['startup_id_candidate'].strip()
        confidence = float(row['confidence_score'])

        # Skip nulls
        if not startup_name or startup_name == '0' or not investor_name:
            continue

        # Try exact match first
        inv_id = None
        startup_id = None

        if investor_name in investor_ids:
            inv_id = investor_name
        else:
            inv_id, inv_score = find_match(investor_name, investor_ids, 0.7)

        if startup_name in startup_ids:
            startup_id = startup_name
        else:
            startup_id, startup_score = find_match(startup_name, startup_ids, 0.6)

        # Only keep good matches
        if inv_id and startup_id:
            real_edges.append({
                'investment_id': f'RAWEDGE_{investor_name}_{startup_name}'.replace(' ', '_')[:80],
                'investor_id': inv_id,
                'startup_id': startup_id,
                'round_name': row.get('relation_type_raw', 'investment'),
                'round_stage': None,
                'announced_date': None,
                'amount': None,
                'currency': None,
                'is_lead': 0,
                'confidence_score': confidence,
                'source_id': 'EDGESECO_RAW',
                'notes': f'From investment_edges_raw.csv'
            })
            matched += 1
        else:
            if not inv_id:
                unmatched_investors.add(investor_name)
            if not startup_id:
                unmatched_startups.add(startup_name)

print(f"   Matched: {matched}")
print(f"   Unmatched investors: {len(unmatched_investors)}")
print(f"   Unmatched startups: {len(unmatched_startups)}")

# 3. Procesar accelerator_portfolio_biotech_latam_2024-2025.csv
print(f"\n3. Procesando accelerator_portfolio_biotech_latam_2024-2025.csv...")

accel_edges = []
accel_matched = 0

with open('staging/accelerator_portfolio_biotech_latam_2024-2025.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)

    for row in reader:
        startup_name = row['name'].strip()
        accelerator_name = row['source_accelerator'].strip()

        # Extract main accelerator name (handle "X + Y" format)
        accel_primary = accelerator_name.split('+')[0].strip()

        # Find matches
        startup_id, startup_score = find_match(startup_name, startup_ids, 0.65)
        inv_id, inv_score = find_match(accel_primary, investor_ids, 0.65)

        if startup_id and inv_id:
            accel_edges.append({
                'investment_id': f'ACCEL_{accel_primary}_{startup_name}'.replace(' ', '_')[:80],
                'investor_id': inv_id,
                'startup_id': startup_id,
                'round_name': 'accelerator',
                'round_stage': 'seed',
                'announced_date': None,
                'amount': None,
                'currency': None,
                'is_lead': 0,
                'confidence_score': 0.75,
                'source_id': 'ACCELERATOR_PORTFOLIO_2024',
                'notes': f'From accelerator portfolio: {accel_primary}'
            })
            accel_matched += 1

print(f"   Matched: {accel_matched}")

# Combinar
all_real_edges = real_edges + accel_edges

print(f"\n4. RESUMEN DE EDGES REALES")
print(f"   investment_edges_raw: {matched}")
print(f"   accelerator_portfolio: {accel_matched}")
print(f"   TOTAL: {len(all_real_edges)}")

# Verificar para duplicados (mismo investor+startup)
duplicates = {}
for edge in all_real_edges:
    key = (edge['investor_id'], edge['startup_id'])
    if key in duplicates:
        duplicates[key] += 1
    else:
        duplicates[key] = 1

unique_edges = len([k for k, v in duplicates.items() if v == 1])
dup_pairs = len([k for k, v in duplicates.items() if v > 1])

print(f"\n5. DEDUPLICATION")
print(f"   Pares únicos: {unique_edges}")
print(f"   Pares duplicados: {dup_pairs}")

# Mostrar ejemplos
print(f"\n6. EJEMPLOS DE EDGES REALES")
for edge in all_real_edges[:10]:
    print(f"   {edge['startup_id']:30} <- {edge['investor_id']:30} ({edge['source_id']})")

print(f"\n7. ESCRIBIENDO A CSV...")
output_path = 'staging/real_capital_edges_extracted.csv'
with open(output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=[
        'investment_id', 'investor_id', 'startup_id', 'round_name', 'round_stage',
        'announced_date', 'amount', 'currency', 'is_lead', 'confidence_score',
        'source_id', 'notes'
    ])
    writer.writeheader()

    # Deduplicar: keep highest confidence for each pair
    seen = {}
    for edge in sorted(all_real_edges, key=lambda x: x['confidence_score'], reverse=True):
        key = (edge['investor_id'], edge['startup_id'])
        if key not in seen:
            writer.writerow(edge)
            seen[key] = True

print(f"   [OK] {len(seen)} edges únicos guardados en {output_path}")

conn.close()

print("\n[DONE] Listos para ingerir datos reales.")
