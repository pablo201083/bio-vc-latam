import sqlite3, pathlib, sys, datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
db = pathlib.Path('db/bio_latam.db')
conn = sqlite3.connect(db)
cur = conn.cursor()
now = datetime.datetime.now(datetime.UTC).isoformat()

def log(entity_id, field, old_val, new_val, reason):
    cur.execute('''INSERT INTO audit_log (timestamp, actor, entity_id, table_name, field, old_value, new_value, reason)
                   VALUES (?,?,?,?,?,?,?,?)''',
                (now, 'human:curador', entity_id, 'startup_extended', field, old_val, new_val, reason))

fixes = [
    ('stamm-ar',     'bio_theme_primary', 'Biomanufacturing & Fermentation Economy',
     'laminar flow bioreactors for decentralized biotech -> Biomanufacturing, not Diagnostics'),
    ('future_biome', 'bio_theme_primary', 'Biomanufacturing & Fermentation Economy',
     'fungi-based precision fermentation prebiotics -> Biomanufacturing, not Food Systems'),
    ('outpost',      'bio_theme_primary', 'Biomanufacturing & Fermentation Economy',
     'wet-lab microbiology + ML platform -> Biomanufacturing, not Diagnostics (cluster CL6 confirmed)'),
]

for sid, field, new_val, reason in fixes:
    cur.execute(f'SELECT {field}, canonical_name FROM startup_extended sx JOIN entities e ON e.entity_id=sx.startup_id WHERE sx.startup_id=?', (sid,))
    row = cur.fetchone()
    if not row:
        print(f'NOT FOUND: {sid}')
        continue
    old_val, name = row
    cur.execute(f'UPDATE startup_extended SET {field}=? WHERE startup_id=?', (new_val, sid))
    log(sid, field, old_val, new_val, reason)
    print(f'OK {name}: {old_val} -> {new_val}')

conn.commit()

from src.clustering import write_dashboard_data
write_dashboard_data(conn)
conn.close()
print('\nDashboard regenerado')
