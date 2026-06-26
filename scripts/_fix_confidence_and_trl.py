"""
Fill bio_theme_confidence and trl_current for the biggest gaps.

Rules:
  bio_theme_confidence:
    - external_auditable_source + no conf → 0.80
    - auto_discovery + no conf → 0.55
    - no basis + no conf → 0.55
  trl_current (numeric 1-9):
    - tech_depth=deep + summary keywords "preclinical/lab/R&D/research/discovery" → 3
    - tech_depth=deep + "prototype/proof-of-concept/pilot" → 4
    - tech_depth=deep + "validated/tested/trial" → 5
    - tech_depth=applied + "pilot/MVP/beta" → 6
    - tech_depth=applied + "commercial/customers/revenue/market" → 7-8
    - tech_depth=applied (default) → 6
    - tech_depth=deep (default) → 4
    - tech_depth=platform → 5
"""
import csv, sqlite3, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
conn = sqlite3.connect(ROOT / "db" / "bio_latam.db")
out = ROOT / "staging" / "entity_enrichments.csv"
src = "swarm_inline_trl_conf_2026-06-26"

rows = []

# ── 1. bio_theme_confidence ─────────────────────────────────────────────────
no_conf = conn.execute("""
    SELECT startup_id, scope_basis, bio_theme_primary
    FROM startup_extended
    WHERE scope_decision='include'
      AND (bio_theme_confidence IS NULL OR bio_theme_confidence = 0)
""").fetchall()

print(f"Startups sin bio_theme_confidence: {len(no_conf)}")
conf_set = 0
for sid, basis, theme in no_conf:
    if basis == 'external_auditable_source':
        conf = 0.80
    elif basis == 'auto_discovery':
        conf = 0.55
    else:
        conf = 0.55
    rows.append([sid, "startup_extended", "bio_theme_confidence", conf,
                 src, 0.9, f"inferred_from_scope_basis:{basis}"])
    conf_set += 1

print(f"  -> {conf_set} confidence values to set")

# ── 2. trl_current for 316 NULL ─────────────────────────────────────────────
DEEP_KEYWORDS = {
    3: ["discovery", "preclinical", "basic research", "r&d", "laboratory", "in vitro", "in silico",
        "computational model", "genomics research", "drug target"],
    4: ["proof of concept", "proof-of-concept", "prototype", "early prototype", "bench",
        "lab-scale", "initial validation", "experimental"],
    5: ["validated", "field trial", "clinical trial", "phase 1", "phase i", "tested",
        "demonstrated", "fermentation scale", "small-scale pilot"],
}
APPLIED_KEYWORDS = {
    6: ["pilot", "mvp", "beta", "early commercial", "first customers", "initial revenue",
        "limited deployment", "scaling up", "pre-commercial"],
    7: ["commercial", "revenue", "customers", "deployed", "sold", "market", "production",
        "subscription", "b2b sales", "enterprise clients"],
    8: ["scale", "thousands of", "hundreds of", "mass production", "major contracts",
        "series a", "series b", "growth stage", "regional expansion"],
}

def infer_trl(tech_depth, summary):
    s = (summary or "").lower()
    if tech_depth == "deep":
        for trl, kws in sorted(DEEP_KEYWORDS.items()):
            if any(kw in s for kw in kws):
                return trl
        # Default deep = 4 (prototype stage for deep tech without explicit signals)
        return 4
    elif tech_depth == "applied":
        for trl, kws in sorted(APPLIED_KEYWORDS.items()):
            if any(kw in s for kw in kws):
                return trl
        # Default applied = 6 (pilot/early commercial)
        return 6
    elif tech_depth == "platform":
        return 5
    else:
        return 5  # fallback

no_trl = conn.execute("""
    SELECT sx.startup_id, sx.tech_depth, sx.startup_summary_en, sx.scope_basis
    FROM startup_extended sx
    WHERE sx.scope_decision='include'
      AND (sx.trl_current_status IS NULL)
""").fetchall()

print(f"\nStartups sin trl_current: {len(no_trl)}")
trl_set = 0
trl_dist = {}
for sid, depth, summary, basis in no_trl:
    trl = infer_trl(depth, summary)
    trl_dist[trl] = trl_dist.get(trl, 0) + 1
    conf = 0.65 if basis == 'external_auditable_source' else 0.50
    rows.append([sid, "startup_extended", "trl_current_status", str(trl),
                 src, conf, f"inferred_from_tech_depth:{depth}+summary_keywords"])
    trl_set += 1

print(f"  -> {trl_set} TRL values to set")
print(f"  TRL distribution: {dict(sorted(trl_dist.items()))}")

# Write
with open(out, "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    for r in rows:
        w.writerow(r)

print(f"\nTotal written: {len(rows)} rows")
conn.close()
