"""
Diagnostica qué entidades en intelligence-data.js no tienen website
y cuáles tienen websites que probablemente fallan en Clearbit.
"""
import sqlite3, sys
sys.stdout.reconfigure(encoding="utf-8")
conn = sqlite3.connect("db/bio_latam.db")

print("=== INVERSORES sin website ===")
rows = conn.execute("""
    SELECT i.investor_id, e.canonical_name, e.country_code, e.website
    FROM investors i
    JOIN entities e ON i.investor_id = e.entity_id
    WHERE e.status != 'excluded'
    ORDER BY e.canonical_name
""").fetchall()

no_web = [(r[0], r[1], r[2]) for r in rows if not r[3]]
with_web = [(r[0], r[1], r[2], r[3]) for r in rows if r[3]]

print(f"  Sin website: {len(no_web)}")
for r in no_web:
    print(f"    {r[0]:<40} {r[1]}")

print(f"\n  Con website: {len(with_web)}")

# Chequear URLs raras que no van a dar logo limpio en Clearbit
print("\n=== Websites NO-DOMINIO-LIMPIO (paths largas, tracxn, etc.) ===")
import re
for r in with_web:
    w = r[3]
    # Dominios de terceros (tracxn, cbinsights, pitchbook, etc.) → no dan logo correcto
    if any(x in w for x in ['tracxn', 'cbinsights', 'pitchbook', 'linkedin', 'crunchbase', 'bloomberg']):
        print(f"    ⚠ {r[0]:<40} {w}")

print("\n=== ENTIDADES no-investor (ESOs, orgs, corporates) sin website ===")
rows2 = conn.execute("""
    SELECT entity_id, canonical_name, entity_type, country_code, website
    FROM entities
    WHERE entity_type != 'investor' AND entity_type != 'startup' AND status != 'excluded'
    ORDER BY canonical_name
""").fetchall()
for r in rows2:
    if not r[4]:
        print(f"    {r[0]:<40} {r[2]:<15} {r[1]}")

conn.close()
