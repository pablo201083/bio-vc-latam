import sqlite3
conn = sqlite3.connect('db/bio_latam.db')
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
for (t,) in tables:
    n = conn.execute(f'SELECT count(*) FROM [{t}]').fetchone()[0]
    print(f'{t}: {n}')

for tname in ('support_edges', 'validation_edges', 'organizations', 'corporates', 'esos'):
    cols = conn.execute(f'PRAGMA table_info({tname})').fetchall()
    if cols:
        print(f'\n{tname} columns: {[c[1] for c in cols]}')
    else:
        print(f'\n{tname}: (no existe)')
conn.close()
