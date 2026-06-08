import sqlite3, sys
sys.stdout.reconfigure(encoding="utf-8")
conn = sqlite3.connect("db/bio_latam.db")

print("=== Buscar spectra en entities ===")
rows = conn.execute(
    "SELECT entity_id, canonical_name, entity_type, country_code, website, status "
    "FROM entities WHERE lower(canonical_name) LIKE '%spectra%' OR lower(entity_id) LIKE '%spectra%'"
).fetchall()
for r in rows:
    print(r)
if not rows:
    print("  (no encontrado)")

print("\n=== PRAGMA table_info(investors) ===")
for c in conn.execute("PRAGMA table_info(investors)").fetchall():
    print(f"  {c[1]} ({c[2]})")

print("\n=== PRAGMA table_info(entities) ===")
for c in conn.execute("PRAGMA table_info(entities)").fetchall():
    print(f"  {c[1]} ({c[2]})")

conn.close()
