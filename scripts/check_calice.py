"""Check calice entities"""
import sqlite3

conn = sqlite3.connect("db/bio_latam.db")

print("=== All calice entities ===")
for r in conn.execute("SELECT entity_id, canonical_name, entity_type, country_code, website FROM entities WHERE entity_id LIKE '%calice%' OR LOWER(canonical_name) LIKE '%calice%'"):
    print(" ", r)

print("\n=== calice_biotech extended ===")
for r in conn.execute("SELECT startup_id, business_one_liner, bio_theme_primary, startup_summary_v1 FROM startup_extended WHERE startup_id='calice_biotech'"):
    print(f"  id: {r[0]}")
    print(f"  one_liner: {r[1]}")
    print(f"  theme: {r[2]}")
    if r[3]:
        print(f"  summary: {r[3][:200]}")

print("\n=== calice-ai-ar extended ===")
for r in conn.execute("SELECT startup_id, business_one_liner, bio_theme_primary, startup_summary_v1 FROM startup_extended WHERE startup_id='calice-ai-ar'"):
    print(f"  id: {r[0]}")
    print(f"  one_liner: {r[1]}")
    print(f"  theme: {r[2]}")
    if r[3]:
        print(f"  summary: {r[3][:200]}")
print("done")
