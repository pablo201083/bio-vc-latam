"""Check Tell Biomarkers and Bayer Legado 2025"""
import sqlite3

conn = sqlite3.connect("db/bio_latam.db")

print("=== Tell entities ===")
for r in conn.execute("""
    SELECT e.entity_id, e.canonical_name, e.entity_type, e.country_code, e.website,
           se.business_one_liner, se.bio_theme_primary
    FROM entities e
    LEFT JOIN startup_extended se ON e.entity_id = se.startup_id
    WHERE e.entity_id = 'tell' OR LOWER(e.canonical_name) LIKE '%tell%'
"""):
    print(" ", r)

print("\n=== Tell edges ===")
for r in conn.execute("SELECT investor_id, startup_id FROM investment_edges WHERE startup_id='tell'"):
    print("  inv:", r)
for r in conn.execute("SELECT source_entity_id, target_entity_id, support_type FROM support_edges WHERE target_entity_id='tell'"):
    print("  sup:", r)

print("\n=== Food For Future / FoodForFuture in DB ===")
for name in ["food for future", "food4future", "food-for-future", "cooltiva", "bzzy", "pastech"]:
    like = f"%{name.replace(' ', '')}%"
    like2 = f"%{name}%"
    r = conn.execute(
        "SELECT entity_id, canonical_name FROM entities WHERE entity_id LIKE ? OR LOWER(canonical_name) LIKE ?", (like, like2)
    ).fetchall()
    if r:
        print(f"  FOUND {name}: {r}")
    else:
        print(f"  not in DB: {name}")
print("done")
