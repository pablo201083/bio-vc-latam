"""
Aplica resultados del enjambre de búsqueda de valuation/funding a startup_extended.
Lee sizing_enrichment_results.json, matchea por nombre canónico, y actualiza via audit.

Campos actualizados:
  - last_funding_at     → last_round_date (si es más reciente que lo existente)
  - valuation_estimate_usd → new_val_estimate_usd_M (si confidence=high y valor presente)

Flags de revisión manual:
  - status=acquired → imprimir lista para curador
  - notes con CORRECCIÓN → imprimir para revisión
"""
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from src.audit import diff_and_log_update

db = sqlite3.connect(ROOT / 'db' / 'bio_latam.db')
db.row_factory = sqlite3.Row

with open(ROOT / 'scripts' / 'oneoff' / 'sizing_enrichment_results.json', encoding='utf-8') as f:
    results = json.load(f)

print(f"{'='*70}")
print(f"APPLY SIZING ENRICHMENT — {len(results)} startups")
print(f"{'='*70}\n")

# Banderas críticas primero
acquired = [r for r in results if r['status'] == 'acquired']
corrections = [r for r in results if 'CORRECCIÓN' in (r['notes'] or '')]

print("⚠️  ADQUIRIDAS (revisar is_bio_universe / scope):")
for r in acquired:
    print(f"   - {r['name']}: {r['notes'][:80]}")

print("\n⚠️  CORRECCIONES DE DATOS BASE:")
for r in corrections:
    print(f"   - {r['name']}: {r['notes'][:100]}")

print(f"\n{'='*70}")
print("APLICANDO ACTUALIZACIONES...")
print(f"{'='*70}\n")

updated = 0
skipped = 0

for r in results:
    name = r['name']

    # Buscar startup_id por nombre canónico (fuzzy: LIKE)
    row = db.execute("""
        SELECT e.entity_id, e.canonical_name,
               se.last_funding_at, se.valuation_estimate_usd, se.valuation_estimate_source
        FROM entities e
        JOIN startup_extended se ON se.startup_id = e.entity_id
        WHERE LOWER(e.canonical_name) LIKE LOWER(?)
        LIMIT 1
    """, (f'%{name.split()[0]}%',)).fetchone()

    # Si no matchea con primera palabra, intentar match exacto parcial
    if not row:
        row = db.execute("""
            SELECT e.entity_id, e.canonical_name,
                   se.last_funding_at, se.valuation_estimate_usd, se.valuation_estimate_source
            FROM entities e
            JOIN startup_extended se ON se.startup_id = e.entity_id
            WHERE LOWER(REPLACE(e.canonical_name, ' ', '')) LIKE LOWER(REPLACE(?, ' ', ''))
            LIMIT 1
        """, (f'%{name[:8]}%',)).fetchone()

    if not row:
        print(f"  [NOT FOUND] {name}")
        skipped += 1
        continue

    entity_id = row['entity_id']
    canonical = row['canonical_name']
    changes = {}

    # Actualizar last_funding_at si tenemos fecha nueva más reciente
    new_date = r.get('last_round_date')
    if new_date and r['confidence'] in ('high', 'medium'):
        existing_date = row['last_funding_at'] or '2000-01'
        # Normalizar: tomar solo YYYY-MM
        existing_ym = existing_date[:7] if existing_date else '2000-01'
        new_ym = new_date[:7]
        if new_ym > existing_ym:
            changes['last_funding_at'] = new_ym + '-01'

    # Actualizar valuation_estimate_usd si tenemos dato de alta confianza
    new_val = r.get('new_val_estimate_usd_M')
    new_src = r.get('new_val_source')
    if new_val and r['confidence'] == 'high' and new_src:
        changes['valuation_estimate_usd'] = new_val
        changes['valuation_estimate_source'] = new_src

    # Actualizar total_raised si tenemos dato confiable y el campo existe
    total_raised = r.get('total_raised_usd_M')
    if total_raised and r['confidence'] == 'high':
        changes['total_raised_usd'] = total_raised

    if not changes:
        print(f"  [NO CHANGES] {canonical} (confidence={r['confidence']}, no new data)")
        skipped += 1
        continue

    # Construir old_vals
    old_vals = {}
    for k in changes:
        old_vals[k] = dict(row).get(k)

    diff_and_log_update(
        db=db,
        table='startup_extended',
        pk_col='startup_id',
        pk_val=entity_id,
        old_vals=old_vals,
        new_vals=changes,
        source=f'haiku_swarm_2026-06-15',
        actor='claude_haiku_swarm'
    )

    changes_str = ', '.join(f"{k}: {old_vals.get(k)} → {v}" for k, v in changes.items())
    print(f"  [UPDATED] {canonical}: {changes_str}")
    updated += 1

db.commit()
db.close()

print(f"\n{'='*70}")
print(f"Resultado: {updated} actualizadas, {skipped} sin cambios / no encontradas")
print(f"\nPróximo paso: python pipeline.py rebuild --phase clustering")
print(f"{'='*70}")
