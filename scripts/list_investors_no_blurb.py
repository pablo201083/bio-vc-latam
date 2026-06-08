import sqlite3, csv, sys
sys.stdout.reconfigure(encoding="utf-8")
conn = sqlite3.connect("db/bio_latam.db")
rows = conn.execute("""
    SELECT i.investor_id, e.canonical_name, e.country_code, e.website,
           i.investor_type, i.geography_focus, i.vertical_focus,
           i.preferred_stages, i.thesis,
           COUNT(ie.investment_id) as edges
    FROM investors i
    JOIN entities e ON i.investor_id = e.entity_id
    LEFT JOIN investment_edges ie ON i.investor_id = ie.investor_id
    WHERE (i.profile_blurb IS NULL OR i.profile_blurb = "")
    GROUP BY i.investor_id
    ORDER BY edges DESC
""").fetchall()
print(f"Investors without blurb: {len(rows)}\n")
for r in rows:
    web = r[3] or ""
    print(f"  {str(r[1]):<35} {str(r[2]):<4} edges={r[9]:>3}  {web[:65]}")
conn.close()
