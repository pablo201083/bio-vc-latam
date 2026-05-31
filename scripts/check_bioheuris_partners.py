"""Check if Bioheuris' partners are in our DB"""
import sqlite3

conn = sqlite3.connect("db/bio_latam.db")

partners = ["argenetics", "aatf", "gdm", "gensus", "genseed", "igenomix"]
print("=== Checking Bioheuris partners ===")
for name in partners:
    like = f"%{name}%"
    r1 = conn.execute(
        "SELECT entity_id, canonical_name, entity_type FROM entities WHERE LOWER(canonical_name) LIKE ? OR entity_id LIKE ?", (like, like)
    ).fetchall()
    if r1:
        print(f"  FOUND {name}: {r1}")
    else:
        print(f"  not in DB: {name}")

# Check existing bioheuris edges
print("\n=== Existing bioheuris edges ===")
for r in conn.execute("SELECT * FROM validation_edges WHERE startup_id='bioheuris'"):
    print("  val:", r)
for r in conn.execute("SELECT * FROM support_edges WHERE target_entity_id='bioheuris' OR source_entity_id='bioheuris'"):
    print("  sup:", r)
for r in conn.execute("SELECT * FROM investment_edges WHERE startup_id='bioheuris'"):
    print("  inv:", r)
