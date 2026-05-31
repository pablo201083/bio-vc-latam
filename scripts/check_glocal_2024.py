"""Check GLOCAL 2024 Game Changers cohort startups"""
import sqlite3

conn = sqlite3.connect("db/bio_latam.db")

print("=== GLOCAL existing investment edges ===")
for r in conn.execute("SELECT investor_id, startup_id, round_stage FROM investment_edges WHERE investor_id='glocal'"):
    print(f"  {r[0]} -> {r[1]} | {r[2]}")

print("\n=== GLOCAL 2024 cohort startups in DB ===")
for name in ["calice-ai-ar", "calice", "zavia_bio", "zavia bio", "bigtrade", "landprint", "bemagro", "blooms"]:
    like = f"%{name}%"
    r1 = conn.execute(
        "SELECT entity_id, canonical_name FROM entities WHERE entity_id LIKE ? OR LOWER(canonical_name) LIKE ?", (like, like)
    ).fetchall()
    if r1:
        # Check for glocal edge
        for entity in r1:
            eid = entity[0]
            has_glocal_inv = conn.execute(
                "SELECT COUNT(*) FROM investment_edges WHERE investor_id='glocal' AND startup_id=?", (eid,)
            ).fetchone()[0]
            has_glocal_sup = conn.execute(
                "SELECT COUNT(*) FROM support_edges WHERE source_entity_id='glocal' AND target_entity_id=?", (eid,)
            ).fetchone()[0]
            marker = "[GLOCAL INV]" if has_glocal_inv else ("[GLOCAL SUP]" if has_glocal_sup else "")
            print(f"  FOUND {name}: {entity} {marker}")

print("\n=== Zavia Bio ===")
for r in conn.execute("SELECT entity_id, canonical_name, entity_type FROM entities WHERE entity_id='zavia_bio' OR entity_id='zavia-bio'"):
    print(" ", r)
for r in conn.execute("SELECT investor_id, startup_id FROM investment_edges WHERE startup_id='zavia_bio' OR startup_id='zavia-bio'"):
    print("  inv:", r)
for r in conn.execute("SELECT source_entity_id, target_entity_id, support_type FROM support_edges WHERE target_entity_id='zavia_bio' OR target_entity_id='zavia-bio'"):
    print("  sup:", r)

print("\n=== calice-ai-ar edges ===")
for r in conn.execute("SELECT investor_id, startup_id FROM investment_edges WHERE startup_id='calice-ai-ar'"):
    print("  inv:", r)
for r in conn.execute("SELECT source_entity_id, target_entity_id, support_type FROM support_edges WHERE target_entity_id='calice-ai-ar'"):
    print("  sup:", r)
print("done")
