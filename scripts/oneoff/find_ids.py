import sqlite3, pathlib, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
db = pathlib.Path('db/bio_latam.db')
conn = sqlite3.connect(db)
cur = conn.cursor()

names = ['Nutrition from Water', 'SaveFruit', 'Zavia Bio', 'Syocin', 'IdeeLab',
         'Exacta BioScience', 'Future Cow', 'Harmony', 'The Live Green Co',
         'Atarraya', 'Bruna', 'Altum Lab']

for name in names:
    cur.execute("""SELECT sx.startup_id, e.canonical_name, sx.cluster_id, sx.bio_theme_primary
                   FROM startup_extended sx JOIN entities e ON e.entity_id=sx.startup_id
                   WHERE lower(e.canonical_name) LIKE lower(?)
                      OR lower(sx.startup_id) LIKE lower(?)""",
                (f'%{name}%', f'%{name.lower().replace(" ","%")}%'))
    rows = cur.fetchall()
    if rows:
        for r in rows:
            print(f'{name:25s} -> {r[0]:35s} CL{r[2]} bio={r[3]}')
    else:
        print(f'{name:25s} -> NOT FOUND')
conn.close()
