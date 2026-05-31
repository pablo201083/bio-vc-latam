"""Delete all ecosystem entities inserted by ingest-orgs so we can re-ingest cleanly."""
import sqlite3
conn = sqlite3.connect('db/bio_latam.db')
conn.execute("PRAGMA journal_mode=WAL")

# Get the org_ids we want to clean
org_ids = [
    'arcap','cab_argentina','aapresid','crea',
    'inia_chile','embrapa','finep','senacyt_panama',
    'bunge','cargill','novonesis','chr_hansen','basf_agricultural','bayer_crop',
]

for oid in org_ids:
    conn.execute("DELETE FROM organizations WHERE org_id=?", (oid,))
    conn.execute("DELETE FROM esos WHERE eso_id=?", (oid,))
    conn.execute("DELETE FROM corporates WHERE corporate_id=?", (oid,))
    conn.execute("DELETE FROM entities WHERE entity_id=?", (oid,))
    conn.execute("DELETE FROM support_edges WHERE source_entity_id=? OR target_entity_id=?", (oid, oid))

conn.commit()
print("Cleaned. Counts:")
for t in ('entities','organizations','esos','corporates','support_edges'):
    n = conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
    print(f"  {t}: {n}")
conn.close()
