import sqlite3, re

conn = sqlite3.connect('db/bio_latam.db')

# Check startup_summary_en
rows = conn.execute("""
    SELECT e.canonical_name, sx.startup_summary_en
    FROM startup_extended sx JOIN entities e ON e.entity_id=sx.startup_id
    WHERE sx.startup_summary_en IS NOT NULL AND sx.startup_summary_en != ''
""").fetchall()

contaminated = [(n, v) for n, v in rows if 'BIO VC LATAM' in (v or '')]
print(f"startup_summary_en hits: {len(contaminated)}")
for name, v in contaminated[:5]:
    m = re.search(r'.{0,30}BIO VC LATAM.{0,60}', v)
    print(f"  {name} -> {m.group() if m else ''}")

# Also check what field the intelligence query actually uses for summary
print("\nColumn check - does startup_extended have startup_summary_en?")
cols = [c[1] for c in conn.execute("PRAGMA table_info(startup_extended)").fetchall()]
en_cols = [c for c in cols if 'summary' in c.lower()]
print(f"Summary columns: {en_cols}")
conn.close()
