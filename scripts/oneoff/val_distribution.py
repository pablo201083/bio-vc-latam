import sqlite3
db = sqlite3.connect('db/bio_latam.db')
rows = db.execute("""
    SELECT valuation_estimate_usd, valuation_estimate_source, canonical_name
    FROM startup_extended se JOIN entities e ON e.entity_id=se.startup_id
    WHERE scope_decision='include'
      AND valuation_estimate_source IN ('gridx_valuation','market_cap','post_money_valuation')
      AND valuation_estimate_usd IS NOT NULL
    ORDER BY valuation_estimate_usd DESC
""").fetchall()
vals = sorted(r[0] for r in rows)
n = len(vals)
print(f"n={n} startups con datos reales")
for b in [1,5,10,25,50,100,200,500,1000]:
    c = sum(1 for v in vals if v >= b)
    print(f">=${b}M: {c} ({c*100//n}%)")
print()
print("Top 20 por valor real:")
for r in rows[:20]:
    print(f"  ${r[0]:>8.1f}M  {r[2][:35]}  ({r[1]})")
db.close()
