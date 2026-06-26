import sqlite3
conn = sqlite3.connect('db/bio_latam.db')
rows = conn.execute("""
    SELECT e.canonical_name, sx.startup_summary_v1
    FROM startup_extended sx JOIN entities e ON e.entity_id=sx.startup_id
    WHERE sx.startup_summary_v1 LIKE '%BIO VC LATAM%'
""").fetchall()
for name, v1 in rows:
    print(name, '->', v1[:300])
conn.close()
