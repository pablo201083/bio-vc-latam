"""Check Seedmatriz connections"""
import sqlite3

conn = sqlite3.connect("db/bio_latam.db")

print("=== Rizobacter/Bioceres in entities ===")
for name in ["rizobacter", "bioceres", "endeavor", "bio4", "hub4", "agidea"]:
    like = f"%{name}%"
    r = conn.execute(
        "SELECT entity_id, canonical_name, entity_type FROM entities WHERE LOWER(canonical_name) LIKE ? OR entity_id LIKE ?", (like, like)
    ).fetchall()
    if r:
        print(f"  FOUND {name}: {r}")

print("\n=== Seedmatriz existing edges ===")
for r in conn.execute("SELECT investor_id, startup_id FROM investment_edges WHERE startup_id='seedmatriz'"):
    print("  inv:", r)
for r in conn.execute("SELECT source_entity_id, target_entity_id, support_type FROM support_edges WHERE target_entity_id='seedmatriz'"):
    print("  sup:", r)

print("\n=== Aceleradora Litoral portfolio ===")
for r in conn.execute("SELECT investor_id, startup_id FROM investment_edges WHERE investor_id='aceleradora_litoral'"):
    print("  inv:", r)
print("done")
