"""
Extrae edges de 'edges_sin_source.csv' - edges verificados con URLs públicas
"""

import sqlite3
import csv

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

# Cargar startup_ids
c.execute('SELECT startup_id FROM startup_extended')
startup_ids = set(row[0] for row in c.fetchall())

print("=" * 80)
print("EXTRAYENDO VERIFIED EDGES DE edges_sin_source.csv")
print("=" * 80)

edges = []
processed = 0
matched = 0

with open('staging/edges_sin_source.csv', 'r', encoding='utf-8', errors='ignore') as f:
    reader = csv.DictReader(f)

    for row in reader:
        if not row:
            continue

        investor_id = (row.get('investor_id') or '').strip().lower().replace(' ', '_')
        startup_id = (row.get('startup_id') or '').strip().lower().replace(' ', '_')
        confidence = row.get('confidence_score', '')
        source_url = row.get('source_url_recuperada', '') or row.get('notes_originales', '')
        accion = row.get('accion', '')

        # Skip si no tiene startup_id o investor_id
        if not startup_id or not investor_id:
            continue

        # Skip si confidence es muy baja
        try:
            conf = float(confidence) if confidence else 0
        except:
            conf = 0

        if conf < 0.85:
            continue

        # Skip si la acción es "remove"
        if 'remove' in accion.lower() or 'exclude' in accion.lower():
            continue

        processed += 1

        # Verificar que startup_id existe en nuestro dataset
        if startup_id in startup_ids and 'http' in source_url.lower():
            edges.append({
                'investment_id': f'VERIFIED_NO_SOURCE_{investor_id}_{startup_id}',
                'investor_id': investor_id,
                'startup_id': startup_id,
                'confidence_score': min(conf, 0.95),  # Cap at 0.95
                'source': f'edges_sin_source: {source_url[:60] if source_url else "official"}'
            })
            matched += 1

print(f"\nProcessed with confidence >= 0.85: {processed}")
print(f"Matched with URL source: {matched}")

# Deduplicar
seen = set()
unique_edges = []

for edge in edges:
    key = (edge['investor_id'], edge['startup_id'])
    if key not in seen:
        unique_edges.append(edge)
        seen.add(key)

print(f"Unique pairs: {len(unique_edges)}")

# Guardar
if unique_edges:
    output_path = 'staging/edges_sin_source_verified.csv'
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
                'investment',
                None,
                None,
                None,
                None,
                0,
                edge['confidence_score'],
                'EDGES_SIN_SOURCE_VERIFIED',
                edge['source']
            ))
            ingested += 1
        except Exception as e:
            print(f"  Error: {e}")

    conn.commit()
    print(f"[OK] {ingested} edges ingiridos")

# Verificar cobertura
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
