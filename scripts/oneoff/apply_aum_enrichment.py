"""Aplica AUM de fondos desde aum_enrichment_results.json a la tabla investors."""
import json, sqlite3, sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from src.audit import diff_and_log_update

db = sqlite3.connect(ROOT / 'db' / 'bio_latam.db')
db.row_factory = sqlite3.Row

with open(ROOT / 'scripts' / 'oneoff' / 'aum_enrichment_results.json', encoding='utf-8') as f:
    results = json.load(f)

updated = skipped = 0
for r in results:
    name = r['name']
    new_aum = r['aum_usd_m']

    # Buscar por nombre (primeras 8 chars)
    row = db.execute("""
        SELECT e.entity_id, e.canonical_name, i.aum_usd_m
        FROM entities e JOIN investors i ON i.investor_id=e.entity_id
        WHERE LOWER(e.canonical_name) LIKE LOWER(?)
        LIMIT 1
    """, (f'%{name[:8]}%',)).fetchone()

    if not row:
        print(f'NOT FOUND: {name}')
        skipped += 1
        continue

    eid, canonical, old_aum = row['entity_id'], row['canonical_name'], row['aum_usd_m']

    if str(old_aum) == str(new_aum):
        print(f'SAME: {canonical} (aum={new_aum}M)')
        skipped += 1
        continue

    diff_and_log_update(
        conn=db, table='investors',
        row_id_col='investor_id', row_id=eid,
        new_values={'aum_usd_m': new_aum},
        actor='claude_haiku_swarm',
        reason=f"AUM web search 2026-06-15: {r['notes']} (confidence={r['confidence']}, year={r['as_of_year']})",
        evidence_url=None
    )
    print(f'UPDATED {canonical}: {old_aum} -> {new_aum}M ({r["confidence"]})')
    updated += 1

db.commit()
db.close()
print(f'\nDone: {updated} updated, {skipped} skipped/not found')
print('Next: python pipeline.py build-atlas')
