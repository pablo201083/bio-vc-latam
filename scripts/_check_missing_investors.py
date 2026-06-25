import sqlite3, pathlib
conn = sqlite3.connect(pathlib.Path(__file__).parent.parent / "db" / "bio_latam.db")
rows = conn.execute("""
    SELECT ie.investor_id, COUNT(*) as cnt
    FROM investment_edges ie
    LEFT JOIN entities e ON e.entity_id = ie.investor_id
    WHERE e.entity_id IS NULL AND ie.investor_id IS NOT NULL AND ie.investor_id != ''
    GROUP BY ie.investor_id
""").fetchall()
conn.close()
print(f"Investors referenciados en edges pero ausentes de entities: {len(rows)}")
for r in rows:
    print(f"  {r[0]}  ({r[1]} edges)")
