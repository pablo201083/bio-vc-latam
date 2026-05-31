"""Check APEXzymes and more"""
import sqlite3

conn = sqlite3.connect("db/bio_latam.db")

print("=== APEXzymes investment edges ===")
for r in conn.execute("SELECT investor_id, startup_id, round_stage, notes FROM investment_edges WHERE startup_id='apexzymes'"):
    print(f"  {r[0]} -> {r[1]} | {r[2]}")
    if r[3]:
        print(f"    notes: {r[3][:100]}")

print("\n=== APEXzymes entity ===")
for r in conn.execute("SELECT entity_id, canonical_name, entity_type, country_code, website FROM entities WHERE entity_id='apexzymes'"):
    print(" ", r)

print("\n=== Nanogrow entity ===")
for r in conn.execute("SELECT entity_id, canonical_name, entity_type, country_code, website FROM entities WHERE entity_id='nanogrow_biotech'"):
    print(" ", r)
for r in conn.execute("SELECT investor_id, startup_id FROM investment_edges WHERE startup_id='nanogrow_biotech'"):
    print("  inv:", r)

print("\n=== Rumina entity ===")
for r in conn.execute("SELECT entity_id, canonical_name, entity_type, country_code, website FROM entities WHERE entity_id='rumina'"):
    print(" ", r)
for r in conn.execute("SELECT investor_id, startup_id FROM investment_edges WHERE startup_id='rumina'"):
    print("  inv:", r)
print("done")
