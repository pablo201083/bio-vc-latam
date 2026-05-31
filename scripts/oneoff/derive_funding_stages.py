"""
derive_funding_stages.py
------------------------
Deriva funding_stage de investment_edges para startups en el mapa semantico
que no tienen funding_stage establecido.

Logica: toma el round_stage mas avanzado de todos los edges del startup.
Solo aplica a startups con cluster_id >= 0 y sin funding_stage.

Ejecutar:
  .venv/Scripts/python.exe derive_funding_stages.py
  .venv/Scripts/python.exe derive_funding_stages.py --dry-run
"""

import sqlite3, pathlib, datetime, sys, argparse
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

parser = argparse.ArgumentParser()
parser.add_argument('--dry-run', action='store_true')
args = parser.parse_args()

DB = pathlib.Path('db/bio_latam.db')
conn = sqlite3.connect(DB)
cur  = conn.cursor()
now  = datetime.datetime.now(datetime.UTC).isoformat()

# Priority order: higher = more advanced
STAGE_PRIORITY = {
    'ipo':            10,
    'private-equity':  9,
    'pipe':            8,
    'series-d':        7,
    'series-c':        6,
    'pre-series-c':    5,
    'growth':          5,
    'series-b':        4,
    'series-a':        3,
    'strategic':       2,
    'seed':            2,
    'accelerator':     1,
    'pre-seed':        1,
    'undisclosed':     0,
    '':                0,
}

# Fetch startups with investment edges but no funding_stage
cur.execute('''
SELECT e.entity_id, e.canonical_name,
       GROUP_CONCAT(DISTINCT COALESCE(ie.round_stage,'')) as round_stages
FROM startup_extended sx JOIN entities e ON e.entity_id=sx.startup_id
JOIN investment_edges ie ON ie.startup_id=e.entity_id
WHERE sx.cluster_id >= 0
  AND (sx.funding_stage IS NULL OR sx.funding_stage = '')
GROUP BY e.entity_id
''')
rows = cur.fetchall()
print(f'Startups con investment_edges pero sin funding_stage: {len(rows)}')
if args.dry_run:
    print('(modo dry-run - no se escribe nada)\n')
print()

derivable = []
skipped = []
for eid, name, stages_str in rows:
    stages = [s.strip() for s in stages_str.split(',') if s.strip()]
    valid = [s for s in stages if s in STAGE_PRIORITY and STAGE_PRIORITY[s] > 0]
    if not valid:
        skipped.append((eid, name, stages))
        continue
    best = max(valid, key=lambda s: STAGE_PRIORITY[s])
    derivable.append((eid, name, best))

# Show distribution
dist = Counter(x[2] for x in derivable)
print('Distribucion derivada:')
for stage, cnt in sorted(dist.items(), key=lambda x: -x[1]):
    print(f'  {stage:<20} {cnt}')
print()

updated = 0
for eid, name, best_stage in derivable:
    print(f'  {name[:45]:<45}  {best_stage}')
    if not args.dry_run:
        cur.execute(
            'UPDATE startup_extended SET funding_stage=? WHERE startup_id=?',
            (best_stage, eid)
        )
        cur.execute(
            '''INSERT INTO audit_log
                 (timestamp, actor, entity_id, table_name, field, old_value, new_value, reason)
               VALUES (?,?,?,?,?,?,?,?)''',
            (now, 'auto:derive_funding_stages', eid, 'startup_extended',
             'funding_stage', None, best_stage,
             f'Derivado del round_stage mas avanzado en investment_edges')
        )
        updated += 1

if skipped:
    print(f'\nSaltados (solo stages ambiguos/vacios): {len(skipped)}')
    for eid, name, stages in skipped[:10]:
        print(f'  {name[:45]:<45}  {stages}')

if not args.dry_run:
    conn.commit()

conn.close()
print()
print(f'Actualizados : {updated}')
print(f'Sin datos    : {len(skipped)}')
