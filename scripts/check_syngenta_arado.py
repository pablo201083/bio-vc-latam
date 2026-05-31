"""Check Syngenta entities and Agrolend/Arado in DB"""
import sqlite3

conn = sqlite3.connect("db/bio_latam.db")

print("=== Syngenta entities ===")
for r in conn.execute("SELECT entity_id, canonical_name, entity_type FROM entities WHERE LOWER(canonical_name) LIKE '%syngenta%' OR entity_id LIKE '%syngenta%'"):
    print(" ", r)

print("\n=== Agrolend/Arado in DB ===")
for name in ["agrolend", "arado", "clicampo"]:
    like = f"%{name}%"
    r1 = conn.execute("SELECT entity_id, canonical_name, entity_type FROM entities WHERE LOWER(canonical_name) LIKE ? OR entity_id LIKE ?", (like, like)).fetchall()
    if r1:
        print(f"  FOUND {name}: {r1}")

print("\n=== Arado existing investment edges ===")
for r in conn.execute("SELECT investor_id, startup_id FROM investment_edges WHERE startup_id='arado'"):
    print("  inv:", r)

print("\n=== Chemtest existing edges ===")
for r in conn.execute("SELECT source_entity_id, target_entity_id, support_type FROM support_edges WHERE target_entity_id='chemtest'"):
    print("  sup:", r)
for r in conn.execute("SELECT investor_id, startup_id FROM investment_edges WHERE startup_id='chemtest'"):
    print("  inv:", r)
print("done")
