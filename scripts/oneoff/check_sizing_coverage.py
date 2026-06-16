import sqlite3
db = sqlite3.connect('db/bio_latam.db')

# n_investors_mapped viene de investment_edges, no de startup_extended
r = db.execute("""
SELECT
  COUNT(*) as total,
  SUM(CASE WHEN se.valuation_estimate_usd IS NOT NULL THEN 1 ELSE 0 END) as con_val,
  SUM(CASE WHEN se.funding_stage IS NOT NULL THEN 1 ELSE 0 END) as con_stage,
  SUM(CASE WHEN se.valuation_estimate_source = 'gridx_valuation' THEN 1 ELSE 0 END) as gridx,
  SUM(CASE WHEN se.valuation_estimate_source = 'stage_estimate' THEN 1 ELSE 0 END) as stage_est,
  SUM(CASE WHEN se.valuation_estimate_source = 'investors_proxy' THEN 1 ELSE 0 END) as inv_proxy,
  SUM(CASE WHEN se.valuation_tier >= 2 THEN 1 ELSE 0 END) as tier2_plus
FROM startup_extended se
WHERE se.is_bio_universe = 1
""").fetchone()

labels = ['total','con_val','con_stage','gridx','stage_est','inv_proxy','tier2+']
for l, v in zip(labels, r):
    pct = f' ({v*100//r[0]}%)' if l != 'total' and r[0] else ''
    print(f'  {l:20s}: {v}{pct}')

# Cuantas tienen inversion mapeada
inv = db.execute("""
SELECT COUNT(DISTINCT ie.startup_id)
FROM investment_edges ie
JOIN startup_extended se ON se.startup_id = ie.startup_id
WHERE se.is_bio_universe = 1
""").fetchone()
print(f'  con_inversores      : {inv[0]} ({inv[0]*100//r[0]}%)')

print()
tiers = db.execute("""
SELECT se.valuation_tier, COUNT(*)
FROM startup_extended se WHERE se.is_bio_universe=1
GROUP BY se.valuation_tier ORDER BY se.valuation_tier
""").fetchall()
print('Valuation tiers:')
for t in tiers:
    print(f'  tier {t[0]}: {t[1]}')

print()
stages = db.execute("""
SELECT se.funding_stage, COUNT(*)
FROM startup_extended se WHERE se.is_bio_universe=1
GROUP BY se.funding_stage ORDER BY COUNT(*) DESC
""").fetchall()
print('Funding stages:')
for s in stages:
    print(f'  {str(s[0]):20s}: {s[1]}')

print()
sources = db.execute("""
SELECT se.valuation_estimate_source, COUNT(*),
       ROUND(AVG(se.valuation_estimate_usd),1),
       ROUND(MIN(se.valuation_estimate_usd),1),
       ROUND(MAX(se.valuation_estimate_usd),1)
FROM startup_extended se
WHERE se.is_bio_universe=1 AND se.valuation_estimate_usd IS NOT NULL
GROUP BY se.valuation_estimate_source ORDER BY COUNT(*) DESC
""").fetchall()
print('Fuentes de valuation:')
for s in sources:
    print(f'  {str(s[0]):25s}: {s[1]} startups | avg=${s[2]}M | [${ s[3]}M – ${s[4]}M]')

# Startups con valuation = NULL: qué stage tienen?
print()
nullval = db.execute("""
SELECT se.funding_stage, COUNT(*)
FROM startup_extended se
WHERE se.is_bio_universe=1 AND se.valuation_estimate_usd IS NULL
GROUP BY se.funding_stage ORDER BY COUNT(*) DESC
""").fetchall()
print('Sin valuation — por stage:')
for s in nullval:
    print(f'  {str(s[0]):20s}: {s[1]}')

db.close()
