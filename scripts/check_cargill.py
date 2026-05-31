"""Check for Agriness/Cargill and corporate mentions in summaries"""
import sqlite3

conn = sqlite3.connect("db/bio_latam.db")

for name in ["agriness", "cargill", "novonesis", "novozymes", "bunge"]:
    like = f"%{name}%"
    r1 = conn.execute(
        "SELECT entity_id, canonical_name, entity_type FROM entities WHERE LOWER(canonical_name) LIKE ?", (like,)
    ).fetchall()
    if r1:
        print(f"ENTITY {name}: {r1}")

print("\nCargill in summaries:")
for r in conn.execute(
    "SELECT startup_id FROM startup_extended WHERE LOWER(startup_summary_v1) LIKE '%cargill%' OR LOWER(startup_summary_en) LIKE '%cargill%'"
):
    print(f"  {r[0]}")

print("Novonesis/Novozymes in summaries:")
for r in conn.execute(
    "SELECT startup_id FROM startup_extended WHERE LOWER(startup_summary_v1) LIKE '%novonesis%' OR LOWER(startup_summary_en) LIKE '%novonesis%' OR LOWER(startup_summary_v1) LIKE '%novozymes%' OR LOWER(startup_summary_en) LIKE '%novozymes%'"
):
    print(f"  {r[0]}")

print("Bunge in summaries:")
for r in conn.execute(
    "SELECT startup_id FROM startup_extended WHERE LOWER(startup_summary_v1) LIKE '%bunge%' OR LOWER(startup_summary_en) LIKE '%bunge%'"
):
    print(f"  {r[0]}")
print("done")
