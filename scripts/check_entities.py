"""Check which new entities/startups exist in the DB"""
import sqlite3

conn = sqlite3.connect("db/bio_latam.db")

# Check bayer
print("=== Bayer entities ===")
for r in conn.execute(
    "SELECT entity_id, canonical_name, entity_type FROM entities WHERE entity_id LIKE '%bayer%' OR LOWER(canonical_name) LIKE '%bayer%'"
):
    print(" ", r)

# Check Bayer Legado winners and finalists
names = [
    "apolo biotech", "apolo-biotech", "growcast", "nativas",
    "agrojusto", "selectivity", "pastech", "b.health", "bhealth",
    "candel", "enteria", "hola tractor", "smart soil",
]
print("\n=== Legado finalists in DB ===")
for name in names:
    like = "%" + name + "%"
    r1 = conn.execute(
        "SELECT entity_id, canonical_name FROM entities WHERE LOWER(canonical_name) LIKE ?", (like,)
    ).fetchall()
    r2 = conn.execute(
        "SELECT se.startup_id, se.business_one_liner FROM startup_extended se WHERE se.startup_id LIKE ? OR LOWER(se.business_one_liner) LIKE ?",
        (like, like),
    ).fetchall()
    if r1 or r2:
        print(f"  FOUND {name}: {r1} | {r2}")

# Scan for apolo in summary
print("\n=== Apolo in summaries ===")
for r in conn.execute(
    "SELECT startup_id, business_one_liner FROM startup_extended WHERE LOWER(business_one_liner) LIKE '%apolo%' OR LOWER(startup_summary_v1) LIKE '%apolo%'"
):
    print(" ", r[0], "|", r[1][:80] if r[1] else "")

print("done")
