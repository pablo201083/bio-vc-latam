"""
GRIDX matching: une el Excel de GRIDX con entities de bio_latam.db.
Estrategia: domain-exact → name-fuzzy.
Output: gridx_match_results.csv con columnas:
  gridx_company, entity_id, canonical_name, match_method, confidence,
  funding_bucket, valuation_bucket, founded_year, country
"""

import re
import sqlite3
import openpyxl
from pathlib import Path
from difflib import SequenceMatcher

ROOT = Path(__file__).parent.parent
XLS = Path(r"F:\Downloads\Analisis GRIDX Deeptech Nueva Ola .xlsx")
DB  = ROOT / "db" / "bio_latam.db"
OUT = ROOT / "staging" / "gridx_match_results.csv"

# ── Funding bucket → stage label ──────────────────────────────────────────────
FUNDING_TIERS = {
    # bucket value (numeric $M) → stage label
    None: None,
    0:    "pre-seed",   # '<1' parsed as 0
    1:    "seed",
    5:    "series-a",
    10:   "series-a",
    15:   "series-a",
    25:   "series-b",
    100:  "series-c+",
    500:  "growth",
    1000: "growth",
}

def parse_bucket(val):
    """'<1' → 0, '#ERROR!' → None, numeric → int"""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return int(val)
    s = str(val).strip()
    if s.startswith("<"):
        return 0
    if s.startswith("#") or s == "":
        return None
    try:
        return int(float(s))
    except ValueError:
        return None

def norm_domain(url):
    """Extract apex domain: 'https://www.stamm.bio' → 'stamm.bio'"""
    if not url:
        return None
    url = str(url).strip().lower()
    url = re.sub(r'^https?://', '', url)
    url = re.sub(r'^www\.', '', url)
    url = url.split('/')[0].split('?')[0].split('#')[0]
    return url or None

def norm_name(s):
    """Lowercase, strip punctuation & common suffixes for fuzzy matching."""
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r'\b(s\.a\.?|inc\.?|ltd\.?|llc\.?|s\.l\.?|spa|sas|bv|ag)\b', '', s)
    s = re.sub(r'[^\w\s]', ' ', s)
    return ' '.join(s.split())

def name_sim(a, b):
    return SequenceMatcher(None, norm_name(a), norm_name(b)).ratio()

# ── Load GRIDX Excel ───────────────────────────────────────────────────────────
wb = openpyxl.load_workbook(XLS, data_only=True)
ws = wb.active

gridx = []
for row in ws.iter_rows(values_only=True):
    company = row[0]
    if not company or not isinstance(company, str) or company == 'Company':
        continue
    gridx.append({
        "company":       company,
        "funding_raw":   row[6],
        "valuation_raw": row[7],
        "country":       row[8],
        "founded":       int(float(row[9])) if row[9] and str(row[9]).strip() not in ('N/A','') else None,
        "description":   row[11],
        "web":           row[12],
        "funding_bucket":  parse_bucket(row[6]),
        "valuation_bucket": parse_bucket(row[7]),
    })

print(f"GRIDX companies loaded: {len(gridx)}")

# ── Load entities from DB ──────────────────────────────────────────────────────
conn = sqlite3.connect(DB)
c = conn.cursor()
c.execute("""
    SELECT e.entity_id, e.canonical_name, e.website, e.status
    FROM entities e
    WHERE e.entity_type = 'startup'
""")
entities = [{"id": r[0], "name": r[1], "web": r[2], "status": r[3]} for r in c.fetchall()]
conn.close()

# Build domain index for fast lookup
domain_idx = {}
for ent in entities:
    d = norm_domain(ent["web"])
    if d:
        domain_idx.setdefault(d, []).append(ent)

print(f"Entities loaded: {len(entities)}")

# ── Match ──────────────────────────────────────────────────────────────────────
results = []
matched_entity_ids = set()

for g in gridx:
    g_domain = norm_domain(g["web"])
    match = None
    method = None
    confidence = 0.0

    # Pass 1: exact domain match
    if g_domain and g_domain in domain_idx:
        candidates = domain_idx[g_domain]
        if len(candidates) == 1:
            match = candidates[0]
            method = "domain-exact"
            confidence = 1.0
        else:
            # Multiple entities share domain — pick best name
            best = max(candidates, key=lambda e: name_sim(g["company"], e["name"]))
            if name_sim(g["company"], best["name"]) > 0.6:
                match = best
                method = "domain-multi-name"
                confidence = name_sim(g["company"], best["name"])

    # Pass 2: fuzzy name match (only if no domain match)
    if not match:
        best_sim = 0.0
        best_ent = None
        for ent in entities:
            sim = name_sim(g["company"], ent["name"])
            if sim > best_sim:
                best_sim = sim
                best_ent = ent
        if best_sim >= 0.92:  # conservative — avoids TerraSense→Terragene style false positives
            match = best_ent
            method = "name-fuzzy"
            confidence = best_sim

    results.append({
        "gridx_company":   g["company"],
        "entity_id":       match["id"]    if match else "",
        "canonical_name":  match["name"]  if match else "",
        "entity_status":   match["status"] if match else "",
        "match_method":    method or "no-match",
        "confidence":      round(confidence, 3),
        "funding_bucket":  g["funding_bucket"],
        "valuation_bucket": g["valuation_bucket"],
        "funding_stage":   FUNDING_TIERS.get(g["funding_bucket"]),
        "founded_year":    g["founded"],
        "country":         g["country"],
        "gridx_web":       g["web"],
    })
    if match:
        matched_entity_ids.add(match["id"])

# ── Stats ──────────────────────────────────────────────────────────────────────
total = len(results)
matched = sum(1 for r in results if r["entity_id"])
domain_m = sum(1 for r in results if "domain" in r["match_method"])
fuzzy_m  = sum(1 for r in results if r["match_method"] == "name-fuzzy")
no_match = sum(1 for r in results if r["match_method"] == "no-match")

print(f"\nMatch results:")
print(f"  Total GRIDX:   {total}")
print(f"  Matched:       {matched} ({100*matched//total}%)")
print(f"    domain:      {domain_m}")
print(f"    name-fuzzy:  {fuzzy_m}")
print(f"  No match:      {no_match}")

# Stage distribution for matched
from collections import Counter
stages = Counter(r["funding_stage"] for r in results if r["entity_id"] and r["funding_stage"])
print(f"\nFunding stage distribution (matched):")
for stage, cnt in sorted(stages.items(), key=lambda x: -x[1]):
    print(f"  {stage}: {cnt}")

# ── Write CSV ──────────────────────────────────────────────────────────────────
import csv
OUT.parent.mkdir(exist_ok=True)
with open(OUT, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)

print(f"\nOutput: {OUT}")
print("\nMatched entities not in our DB (new discoveries):")
unmatched = [r for r in results if not r["entity_id"]]
for r in unmatched[:20]:
    print(f"  {r['gridx_company']} | {r['country']} | funding: {r['funding_bucket']}M")
