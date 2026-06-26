"""Infer valuation_tier from funding_stage + funding_bucket_usd for 105 missing."""
import csv, sqlite3, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
conn = sqlite3.connect(ROOT / "db" / "bio_latam.db")
out = ROOT / "staging" / "entity_enrichments.csv"
src = "swarm_inline_valuation_2026-06-26"

# See existing tier values
tiers = conn.execute("""
    SELECT DISTINCT valuation_tier FROM startup_extended
    WHERE valuation_tier IS NOT NULL AND valuation_tier != ''
    ORDER BY valuation_tier
""").fetchall()
print("Existing tiers:", [t[0] for t in tiers])

# See funding_stage values
stages = conn.execute("""
    SELECT DISTINCT funding_stage, COUNT(*) as n
    FROM startup_extended WHERE scope_decision='include'
    GROUP BY funding_stage ORDER BY n DESC LIMIT 15
""").fetchall()
print("\nFunding stages:")
for s, n in stages:
    print(f"  {str(s):<30} {n}")

# Missing valuation_tier
missing = conn.execute("""
    SELECT sx.startup_id, e.canonical_name, sx.funding_stage, sx.funding_bucket_usd,
           sx.trl_current_status, sx.tech_depth, sx.bio_theme_primary
    FROM startup_extended sx
    JOIN entities e ON e.entity_id = sx.startup_id
    WHERE sx.scope_decision='include'
      AND (sx.valuation_tier IS NULL OR sx.valuation_tier = '')
    ORDER BY e.canonical_name
""").fetchall()

print(f"\nSin valuation_tier: {len(missing)}")

conn.close()

# Mapping logic
# Tiers observed: micro (<$1M), seed_range ($1M-$5M), early ($5M-$20M),
#                 mid ($20M-$100M), growth ($100M+), unknown
STAGE_TO_TIER = {
    "pre_seed": "1",
    "pre-seed": "1",
    "preseed": "1",
    "accelerator": "1",
    "angel": "1",
    "grant": "1",
    "seed": "1.5",
    "seed+": "1.5",
    "series_a": "2",
    "series-a": "2",
    "series a": "2",
    "series_b": "3",
    "series-b": "3",
    "series b": "3",
    "series_c": "4",
    "series-c": "4",
    "series-c+": "4",
    "series c": "4",
    "series_d": "4",
    "growth": "4",
    "ipo": "4",
    "exit": "4",
}

rows = []
tier_dist = {}
no_stage = 0

for sid, name, stage, bucket, trl, depth, theme in missing:
    stage_key = (stage or "").lower().replace("-", "_").strip()
    tier = STAGE_TO_TIER.get(stage_key)

    if not tier:
        # Infer from bucket
        if bucket and "$" in str(bucket):
            b = str(bucket).lower()
            if "100m" in b or "500m" in b or ">100" in b:
                tier = "growth"
            elif "20m" in b or "50m" in b or ">20" in b:
                tier = "mid"
            elif "5m" in b or "10m" in b or ">5" in b:
                tier = "early"
            elif "1m" in b or "2m" in b or ">1" in b:
                tier = "seed_range"
            else:
                tier = "micro"
        else:
            # Infer from TRL as last resort
            trl_n = int(trl) if trl and str(trl).isdigit() else 5
            if trl_n >= 7:
                tier = "1.5"
            else:
                tier = "1"
            no_stage += 1

    tier_dist[tier] = tier_dist.get(tier, 0) + 1
    conf = 0.50 if no_stage else 0.65
    rows.append([sid, "startup_extended", "valuation_tier", tier,
                 src, conf, f"inferred_from_stage:{stage_key or 'none'}"])

print(f"Tier distribution: {dict(sorted(tier_dist.items()))}")
print(f"Inferred from TRL (no stage): {no_stage}")

with open(out, "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    for r in rows:
        w.writerow(r)

print(f"\nWritten {len(rows)} rows")
