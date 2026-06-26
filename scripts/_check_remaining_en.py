import sqlite3, re
conn = sqlite3.connect('db/bio_latam.db')
rows = conn.execute("""
    SELECT e.canonical_name, sx.startup_summary_en
    FROM startup_extended sx JOIN entities e ON e.entity_id=sx.startup_id
    WHERE sx.startup_summary_en LIKE '%BIO VC LATAM%'
""").fetchall()
for name, v in rows:
    m = re.search(r'.{0,30}BIO VC LATAM.{0,80}', v or '')
    print(name, '->', m.group() if m else '')
conn.close()
