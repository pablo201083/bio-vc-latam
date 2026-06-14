"""
Extrae edges 'funded_by' del grafo Gephi completo.
Este archivo tiene todas las aristas del ecosistema LATAM biotech.
"""

import sqlite3
import csv
from difflib import SequenceMatcher

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

# Cargar startup_ids e investor_ids
c.execute('SELECT startup_id FROM startup_extended')
startup_ids = set(row[0] for row in c.fetchall())

c.execute('SELECT investor_id FROM investors')
investor_ids = set(row[0] for row in c.fetchall())

def fuzzy_match(name, candidates, threshold=0.65):
    best_match = None
    best_score = threshold
    for candidate in candidates:
        score = SequenceMatcher(None, name.lower(), candidate.lower()).ratio()
        if score > best_score:
            best_score = score
            best_match = candidate
    return best_match, best_score

print("=" * 80)
print("EXTRAYENDO FUNDED_BY EDGES DEL GRAFO GEPHI COMPLETO")
print("=" * 80)

edges = []
processed = 0
matched = 0
skipped = 0

with open('staging/full_gephi_graph/edges_full.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)

    for row in reader:
        edge_type = row.get('d12', '')  # tipo de relación

        # Solo extraer "funded_by" (startup financiada por inversor)
        if edge_type == 'funded_by':
            source_id = row.get('source', '').strip().lower()
            target_id = row.get('target', '').strip().lower()

            if not source_id or not target_id:
                continue

            processed += 1

            # target debería ser inversor, source debería ser startup
            # Verificar en nuestras listas
            startup_id = None
            investor_id = None

            # Buscar startup en source
            if source_id in startup_ids:
                startup_id = source_id
            else:
                match, score = fuzzy_match(source_id, startup_ids, 0.75)
                if match and score > 0.80:
                    startup_id = match

            # Buscar inversor en target
            if target_id in investor_ids:
                investor_id = target_id
            else:
                match, score = fuzzy_match(target_id, investor_ids, 0.75)
                if match and score > 0.80:
                    investor_id = match

            if startup_id and investor_id:
                edges.append({
                    'investment_id': f'GEPHI_{startup_id}_{investor_id}',
                    'investor_id': investor_id,
                    'startup_id': startup_id,
                    'confidence_score': 0.85,
                    'source': 'full_gephi_graph (network)'
                })
                matched += 1
            else:
                skipped += 1

print(f"\nProcessed: {processed} funded_by edges")
print(f"Matched: {matched}")
print(f"Skipped: {skipped} (not in DB)")

# Deduplicar
seen = set()
unique_edges = []

for edge in edges:
    key = (edge['investor_id'], edge['startup_id'])
    if key not in seen:
        unique_edges.append(edge)
        seen.add(key)

print(f"\nUnique pairs: {len(unique_edges)}")

# Guardar
if unique_edges:
    output_path = 'staging/gephi_funded_by_edges.csv'
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['investment_id', 'investor_id', 'startup_id', 'confidence_score', 'source'])
        writer.writeheader()
        writer.writerows(unique_edges)

    print(f"[OK] Guardado en {output_path}")

    # Ingeirir
    print("\nIngiriendo a DB...")

    ingested = 0
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
                'funding',
                None,
                None,
                None,
                None,
                0,
                edge['confidence_score'],
                'GEPHI_NETWORK',
                edge['source']
            ))
            ingested += 1
        except Exception as e:
            print(f"  Error: {e}")

    conn.commit()
    print(f"[OK] {ingested} edges ingiridos")

# Verificar cobertura final
c.execute('''
SELECT COUNT(DISTINCT startup_id)
FROM investment_edges
WHERE startup_id IN (
  SELECT startup_id FROM startup_extended WHERE cluster_id >= 0
)
''')
covered = c.fetchone()[0]

c.execute('SELECT COUNT(*) FROM investment_edges')
total = c.fetchone()[0]

print(f"\nESTADO FINAL:")
print(f"  Total edges: {total}")
print(f"  Startups clustered con edges: {covered}/606 ({100*covered//606}%)")

conn.close()
