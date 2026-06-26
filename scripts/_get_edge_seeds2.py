"""Find startups referenced in investment_edges but absent from entities."""
import sqlite3, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
conn = sqlite3.connect(ROOT / "db" / "bio_latam.db")

# Startups missing from entities
missing_startups = conn.execute("""
    SELECT DISTINCT ie.startup_id
    FROM investment_edges ie
    LEFT JOIN entities e ON e.entity_id = ie.startup_id
    WHERE e.entity_id IS NULL AND ie.startup_id IS NOT NULL AND ie.startup_id != ''
""").fetchall()

# Investors missing from entities
missing_investors = conn.execute("""
    SELECT DISTINCT ie.investor_id, COUNT(*) as n
    FROM investment_edges ie
    LEFT JOIN entities e ON e.entity_id = ie.investor_id
    WHERE e.entity_id IS NULL AND ie.investor_id IS NOT NULL AND ie.investor_id != ''
    GROUP BY ie.investor_id
""").fetchall()

conn.close()

print(f"Startups en investment_edges sin entidad: {len(missing_startups)}")
for r in missing_startups:
    print(f"  startup: {r[0]}")

print(f"\nInversores en investment_edges sin entidad: {len(missing_investors)}")
for inv_id, n in missing_investors:
    print(f"  investor: {inv_id} ({n} edges)")
