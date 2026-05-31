"""Check CONICET startups from BioArgentina 2021 against DB"""
import sqlite3

conn = sqlite3.connect("db/bio_latam.db")

names = [
    ("chemtest", ["chemtest"]),
    ("ckapur", ["ckapur", "kapur"]),
    ("infira", ["infira"]),
    ("microgenesis", ["microgenesis"]),
    ("argentag", ["argentag"]),
    ("inmunova", ["inmunova"]),
    ("food4you", ["food4you", "food 4 you"]),
]

print("=== CONICET BioArgentina 2021 startups in DB ===")
for name, aliases in names:
    found = []
    for alias in aliases:
        like = f"%{alias}%"
        r1 = conn.execute(
            "SELECT entity_id, canonical_name, entity_type FROM entities WHERE LOWER(canonical_name) LIKE ? OR entity_id LIKE ?",
            (like, like)
        ).fetchall()
        found.extend(r1)
    if found:
        print(f"  FOUND {name}: {found}")
    else:
        print(f"  not in DB: {name}")

# Now also check which AR startups are explicitly CONICET EBTs (from our summary data)
print("\n=== CONICET mentions in AR startup summaries ===")
for r in conn.execute("""
    SELECT se.startup_id, e.canonical_name
    FROM startup_extended se
    JOIN entities e ON se.startup_id = e.entity_id
    WHERE e.country_code = 'AR'
      AND (LOWER(se.startup_summary_v1) LIKE '%conicet%' OR LOWER(se.startup_summary_en) LIKE '%conicet%')
    ORDER BY se.data_quality_score DESC
    LIMIT 20
"""):
    print(f"  {r[0]:35} | {r[1]}")
