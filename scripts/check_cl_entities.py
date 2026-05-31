"""Check Chile-related entities for CORFO connections"""
import sqlite3

conn = sqlite3.connect("db/bio_latam.db")

print("=== Chile funding entities ===")
for name in ["chile global", "ganesha", "anid", "corfo", "startup chile", "innova", "sercotec"]:
    like = f"%{name}%"
    r = conn.execute(
        "SELECT entity_id, canonical_name, entity_type FROM entities WHERE LOWER(canonical_name) LIKE ? OR entity_id LIKE ?",
        (like, like)
    ).fetchall()
    if r:
        print(f"  FOUND {name}: {r}")

# Check matchetune website details
print("\n=== Matchetune in DB ===")
for r in conn.execute("SELECT se.startup_id, e.canonical_name, e.website, e.country_code FROM startup_extended se JOIN entities e ON se.startup_id=e.entity_id WHERE se.startup_id='matchetune'"):
    print(" ", r)
for r in conn.execute("SELECT * FROM investment_edges WHERE startup_id='matchetune'"):
    print("  inv:", r[1], "->", r[2], r[3])
for r in conn.execute("SELECT * FROM support_edges WHERE target_entity_id='matchetune'"):
    print("  sup:", r)

# Check lemu
print("\n=== Lemu in DB ===")
for r in conn.execute("SELECT * FROM investment_edges WHERE startup_id='lemu'"):
    print("  inv:", r[1], "->", r[2])
for r in conn.execute("SELECT * FROM support_edges WHERE target_entity_id='lemu'"):
    print("  sup:", r)
print("done")
