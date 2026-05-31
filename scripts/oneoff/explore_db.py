import sqlite3
conn = sqlite3.connect("db/bio_latam.db")

# Investment edges per startup
print("=== Investment rounds per startup (top 20) ===")
rows = conn.execute("""
    SELECT e.canonical_name, sx.valuation_tier, sx.quality_band,
           COUNT(ie.investment_id) as n_rounds,
           COUNT(DISTINCT ie.round_name) as n_stages,
           MAX(ie.amount) as max_amount
    FROM startup_extended sx
    JOIN entities e ON e.entity_id = sx.startup_id
    LEFT JOIN investment_edges ie ON ie.startup_id = sx.startup_id
    WHERE sx.scope_decision='include'
    GROUP BY sx.startup_id
    ORDER BY n_rounds DESC, sx.valuation_tier DESC NULLS LAST
    LIMIT 20
""").fetchall()
for r in rows:
    print(f"  {r[0][:38]:38s} tier={str(r[1]):4s} band={r[2]:6s} rounds={r[3]} stages={r[4]} max_amt={r[5]}")

print()
print("=== round_stage distribution ===")
stages = conn.execute("SELECT round_stage, COUNT(*) FROM investment_edges GROUP BY round_stage ORDER BY COUNT(*) DESC").fetchall()
for s in stages: print(f"  {s[0]}: {s[1]}")

print()
print("=== valuation_tier + n_rounds matrix ===")
tiers = conn.execute("""
    SELECT sx.valuation_tier, COUNT(DISTINCT sx.startup_id) as n_startups,
           SUM(CASE WHEN ie.investment_id IS NOT NULL THEN 1 ELSE 0 END) as total_rounds
    FROM startup_extended sx
    LEFT JOIN investment_edges ie ON ie.startup_id = sx.startup_id
    WHERE sx.scope_decision='include'
    GROUP BY sx.valuation_tier ORDER BY sx.valuation_tier
""").fetchall()
for t in tiers: print(f"  tier={t[0]} startups={t[1]} rounds={t[2]}")
