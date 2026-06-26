"""Get external edge seeds: target_ids in investment_edges not in entities."""
import sqlite3, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
conn = sqlite3.connect(ROOT / "db" / "bio_latam.db")
rows = conn.execute("""
    SELECT DISTINCT ie.target_id, ie.target_name, ie.investor_id
    FROM investment_edges ie
    LEFT JOIN entities e ON e.entity_id = ie.target_id
    WHERE e.entity_id IS NULL
      AND ie.target_id IS NOT NULL AND ie.target_id != ''
    ORDER BY ie.target_id
""").fetchall()
conn.close()
print(f"External edge seeds: {len(rows)}")
for tid, tname, inv in rows:
    print(f"{tid}|{tname or ''}|{inv}")
