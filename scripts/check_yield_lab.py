"""Check which Yield Lab LATAM portfolio companies and ANPCYT Rosario startups are in DB"""
import sqlite3

conn = sqlite3.connect("db/bio_latam.db")

# Yield Lab portfolio
yield_lab_companies = [
    "bemagro", "bem agro", "incluirtec", "culttivo", "produzindo certo",
    "cerradox", "cerrado", "verqor", "blooms", "agricapital",
    "phagelab", "phage lab", "kigui", "beeflow", "courageous land"
]

print("=== Yield Lab Portfolio in DB ===")
for name in yield_lab_companies:
    like = "%" + name + "%"
    r1 = conn.execute(
        "SELECT entity_id, canonical_name, entity_type FROM entities WHERE LOWER(canonical_name) LIKE ?", (like,)
    ).fetchall()
    if r1:
        print(f"  FOUND {name}: {r1}")

# Rosario ANPCYT startups
rosario_startups = ["taxon", "mycorium", "hialos", "hygeia", "exo+", "exo plus"]
print("\n=== Rosario ANPCYT Startups in DB ===")
for name in rosario_startups:
    like = "%" + name + "%"
    r1 = conn.execute(
        "SELECT entity_id, canonical_name, entity_type FROM entities WHERE LOWER(canonical_name) LIKE ?", (like,)
    ).fetchall()
    if r1:
        print(f"  FOUND {name}: {r1}")
    # also check startup_extended IDs
    r2 = conn.execute(
        "SELECT startup_id FROM startup_extended WHERE startup_id LIKE ?", (like,)
    ).fetchall()
    if r2:
        print(f"  STARTUP_EXT {name}: {r2}")

# Check existing Yield Lab investments
print("\n=== Existing Yield Lab investments ===")
for r in conn.execute(
    "SELECT investment_id, investor_id, startup_id FROM investment_edges WHERE investor_id LIKE '%yield%'"
):
    print(" ", r)

print("done")
