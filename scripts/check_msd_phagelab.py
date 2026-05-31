"""Check MSD, ANID entities and PhageLab/Lab4U existing edges"""
import sqlite3

conn = sqlite3.connect("db/bio_latam.db")

print("=== MSD/Merck in entities ===")
for r in conn.execute("SELECT entity_id, canonical_name, entity_type FROM entities WHERE LOWER(canonical_name) LIKE '%msd%' OR LOWER(canonical_name) LIKE '%merck%' OR entity_id LIKE '%msd%' OR entity_id LIKE '%merck%'"):
    print(" ", r)

print("\n=== ANID in entities ===")
for r in conn.execute("SELECT entity_id, canonical_name, entity_type FROM entities WHERE LOWER(canonical_name) LIKE '%anid%' OR entity_id LIKE '%anid%'"):
    print(" ", r)

print("\n=== PhageLab existing edges ===")
for r in conn.execute("SELECT * FROM support_edges WHERE target_entity_id='phagelab' OR source_entity_id='phagelab'"):
    print("  sup:", r)
for r in conn.execute("SELECT * FROM validation_edges WHERE startup_id='phagelab'"):
    print("  val:", r)
for r in conn.execute("SELECT * FROM investment_edges WHERE startup_id='phagelab'"):
    print("  inv:", r[1], "->", r[2])

print("\n=== Lab4U in DB ===")
for r in conn.execute("SELECT entity_id, canonical_name, entity_type FROM entities WHERE LOWER(canonical_name) LIKE '%lab4u%' OR entity_id LIKE '%lab4u%'"):
    print(" ", r)
print("done")
