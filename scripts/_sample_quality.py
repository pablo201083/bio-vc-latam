import sqlite3
conn = sqlite3.connect('db/bio_latam.db')
rows = conn.execute("""
    SELECT e.canonical_name, sx.startup_summary_v1, sx.startup_summary_en, sx.business_one_liner
    FROM entities e JOIN startup_extended sx ON sx.startup_id = e.entity_id
    WHERE sx.scope_decision = 'include'
    AND sx.startup_summary_v1 IS NOT NULL
    AND sx.startup_summary_v1 != ''
    ORDER BY sx.computed_quality_score DESC
    LIMIT 6
""").fetchall()
for name, v1, en, ol in rows:
    print(f"=== {name} ===")
    print(f"v1:  {(v1 or '')[:200]}")
    print(f"en:  {(en or '')[:200]}")
    print(f"ol:  {(ol or '')[:80]}")
    print()
conn.close()
