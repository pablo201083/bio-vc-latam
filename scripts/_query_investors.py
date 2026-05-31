"""Query investors by country/type to identify membership candidates."""
import sqlite3
conn = sqlite3.connect('db/bio_latam.db')

print("=== Inversores por pais y tipo ===\n")
for country in ['AR', 'BR', 'MX', 'CL', 'CO', 'PE', 'UY']:
    rows = conn.execute("""
        SELECT e.entity_id, e.canonical_name, e.country_code,
               i.investor_type, e.website
        FROM entities e JOIN investors i ON i.investor_id=e.entity_id
        WHERE e.country_code=? AND e.status!='excluded'
        ORDER BY e.canonical_name
    """, (country,)).fetchall()
    if rows:
        print(f"[{country}] ({len(rows)} fondos)")
        for r in rows:
            print(f"  {r[0]:<30} {r[3]:<22} {r[4] or ''}")
        print()

print("\n=== Inversores sin pais asignado ===")
rows = conn.execute("""
    SELECT e.entity_id, e.canonical_name, i.investor_type, i.geography_focus
    FROM entities e JOIN investors i ON i.investor_id=e.entity_id
    WHERE (e.country_code IS NULL OR e.country_code='') AND e.status!='excluded'
    ORDER BY e.canonical_name LIMIT 30
""").fetchall()
for r in rows:
    print(f"  {r[0]:<30} {r[2]:<22} geo={r[3] or ''}")

conn.close()
