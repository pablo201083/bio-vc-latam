"""
Extrae edges VERIFICADOS de investment_rounds.csv
(fuente: portfolio pages oficiales de VCs)
"""

import sqlite3
import csv
from difflib import SequenceMatcher

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

# Cargar startup_ids
c.execute('SELECT startup_id FROM startup_extended')
startup_ids = set(row[0] for row in c.fetchall())

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
print("EXTRAYENDO EDGES DE investment_rounds.csv (FUENTES VERIFICADAS)")
print("=" * 80)

edges = []
processed = 0
matched = 0

# Leer investment_rounds.csv
with open('staging/investment_rounds.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)

    for row in reader:
        investor_id = row.get('investor_id', '').strip()
        startup_id = row.get('startup_id', '').strip()
        source = row.get('notes', '') or row.get('source_url', '')

        # Skip nulls
        if not startup_id or not investor_id:
            continue

        # Solo usar si tiene fuente verificada (portfolio oficial)
        if 'official portfolio' in source.lower() or 'official' in source.lower():
            processed += 1

            # Normalizar investor_id
            investor_id_clean = investor_id.lower().replace(' ', '_')

            # Verificar que startup_id existe en nuestro dataset
            if startup_id in startup_ids:
                confidence = 0.95  # Portfolio oficial = muy alta confianza
                edges.append({
                    'investment_id': f'VERIFIED_{investor_id_clean}_{startup_id}',
                    'investor_id': investor_id_clean,
                    'startup_id': startup_id,
                    'confidence_score': confidence,
                    'source': f'investment_rounds: official portfolio'
                })
                print(f"  [OK] {investor_id:25} -> {startup_id:30} (0.95)")
                matched += 1
            else:
                print(f"  [NOT IN DB] {startup_id:30}")

print(f"\n{matched}/{processed} edges con fuente verificada")

print("\n" + "=" * 80)
print(f"TOTAL: {len(edges)} edges verificados")
print("=" * 80)

if edges:
    # Guardar
    output_path = 'staging/investment_rounds_verified_edges.csv'
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['investment_id', 'investor_id', 'startup_id', 'confidence_score', 'source'])
        writer.writeheader()
        writer.writerows(edges)

    print(f"Guardado en {output_path}")

    # Ingeirir
    print("\nIngiriendo a DB...")

    ingested = 0
    for edge in edges:
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
                'round',
                None,
                None,
                None,
                None,
                0,
                edge['confidence_score'],
                'INVESTMENT_ROUNDS_VERIFIED',
                edge['source']
            ))
            ingested += 1
        except Exception as e:
            print(f"  Error: {e}")

    conn.commit()
    print(f"[OK] {ingested} edges ingiridos")

# Verificar estado final
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
