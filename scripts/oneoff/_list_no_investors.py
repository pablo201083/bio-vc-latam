import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('db/bio_latam.db')
conn.row_factory = sqlite3.Row

rows = conn.execute("""
    SELECT e.entity_id, e.canonical_name, e.country_code,
           sx.funding_stage, sx.bio_theme_primary
    FROM entities e
    JOIN startup_extended sx ON e.entity_id = sx.startup_id
    WHERE NOT EXISTS (SELECT 1 FROM investment_edges ie WHERE ie.startup_id = e.entity_id)
    AND e.status != 'excluded'
    AND sx.scope_decision = 'include'
    ORDER BY
        CASE sx.funding_stage
            WHEN 'Series C' THEN 1 WHEN 'Series B' THEN 2 WHEN 'Series A' THEN 3
            WHEN 'Seed' THEN 4 WHEN 'Pre-Seed' THEN 5
            ELSE 6 END,
        e.country_code, e.canonical_name
""").fetchall()

print(f'Total without investors: {len(rows)}')
from collections import defaultdict
by_stage = defaultdict(list)
for r in rows:
    by_stage[r['funding_stage'] or 'Unknown'].append(r)

order = ['Series C','Series B','Series A','Seed','Pre-Seed','Unknown']
for stage in order:
    items = by_stage.get(stage, [])
    if not items: continue
    print(f'--- {stage} ({len(items)}) ---')
    for r in items:
        print(f'  {r["entity_id"]:40} {r["country_code"]:4} {r["canonical_name"]}')
    print()

with open('scripts/oneoff/_no_inv_list.txt', 'w', encoding='utf-8') as f:
    f.write(f'Total: {len(rows)}\n')
    for stage in order:
        items = by_stage.get(stage, [])
        if not items: continue
        f.write(f'\n--- {stage} ({len(items)}) ---\n')
        for r in items:
            f.write(f'  {r["entity_id"]:40} {r["country_code"]:4} {r["canonical_name"]}\n')
