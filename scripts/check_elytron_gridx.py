"""Check elytron_biotech -> gridx investment and NanoInGreen entity"""
import sqlite3

conn = sqlite3.connect("db/bio_latam.db")

print("=== elytron_biotech investment edges ===")
for r in conn.execute("SELECT * FROM investment_edges WHERE startup_id='elytron_biotech'"):
    print(" ", r)

print("\n=== nanoingreen investment edges ===")
for r in conn.execute("SELECT * FROM investment_edges WHERE startup_id='nanoingreen'"):
    print(" ", r)

# Check if Nestle is in entities
print("\n=== Nestle in entities ===")
for r in conn.execute("SELECT entity_id, canonical_name, entity_type FROM entities WHERE LOWER(canonical_name) LIKE '%nestl%'"):
    print(" ", r)

# Check nanoingreen entity
print("\n=== nanoingreen entity ===")
for r in conn.execute("SELECT entity_id, canonical_name, entity_type, country_code FROM entities WHERE entity_id='nanoingreen'"):
    print(" ", r)

# Check if microgenesis website mentions any partners
print("\n=== microgenesis entity ===")
for r in conn.execute("SELECT entity_id, canonical_name, website FROM entities WHERE entity_id='microgenesis'"):
    print(" ", r)
