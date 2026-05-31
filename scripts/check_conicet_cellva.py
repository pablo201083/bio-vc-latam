"""Check CONICET entity and Cellva investors"""
import sqlite3

conn = sqlite3.connect("db/bio_latam.db")

print("=== CONICET in entities ===")
for r in conn.execute("SELECT entity_id, canonical_name, entity_type FROM entities WHERE LOWER(canonical_name) LIKE '%conicet%' OR entity_id LIKE '%conicet%'"):
    print(" ", r)

print("\n=== AIR Capital / Air Capital in entities ===")
for r in conn.execute("SELECT entity_id, canonical_name, entity_type FROM entities WHERE LOWER(canonical_name) LIKE '%air capital%' OR LOWER(canonical_name) LIKE '%aircapital%' OR entity_id LIKE '%air%capital%'"):
    print(" ", r)

print("\n=== Existing microgenesis edges ===")
for r in conn.execute("SELECT * FROM support_edges WHERE target_entity_id='microgenesis' OR source_entity_id='microgenesis'"):
    print("  sup:", r)
for r in conn.execute("SELECT * FROM investment_edges WHERE startup_id='microgenesis'"):
    print("  inv:", r)

print("\n=== Cellva in entities ===")
for r in conn.execute("SELECT entity_id, canonical_name, entity_type FROM entities WHERE entity_id='cellva' OR LOWER(canonical_name) LIKE '%cellva%'"):
    print(" ", r)
for r in conn.execute("SELECT * FROM investment_edges WHERE startup_id='cellva'"):
    print("  inv:", r)
print("done")
