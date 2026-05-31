"""Check Arado and Agrolend investment edges"""
import sqlite3

conn = sqlite3.connect("db/bio_latam.db")

print("=== Arado investment edges ===")
for r in conn.execute("SELECT investor_id, startup_id, round_stage, announced_date, notes FROM investment_edges WHERE startup_id='arado'"):
    print(f"  inv: {r[0]} | {r[1]} | stage={r[2]} | date={r[3]}")
    if r[4]:
        print(f"    notes: {r[4][:100]}")

print("\n=== Agrolend investment edges ===")
for r in conn.execute("SELECT investor_id, startup_id, round_stage, announced_date, notes FROM investment_edges WHERE startup_id='agrolend'"):
    print(f"  inv: {r[0]} | {r[1]} | stage={r[2]} | date={r[3]}")

print("\n=== Acre Venture Partners in entities ===")
for r in conn.execute("SELECT entity_id, canonical_name, entity_type FROM entities WHERE LOWER(canonical_name) LIKE '%acre%' OR entity_id LIKE '%acre%'"):
    print(" ", r)

print("done")
