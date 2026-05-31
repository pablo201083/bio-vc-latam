"""
Mine startup summaries for mentions of grants and public funding bodies.
Outputs candidates for new support_edges (grant_recipient) and validation_edges.
"""
import sqlite3
import re
import sys
sys.stdout.reconfigure(encoding="utf-8")

conn = sqlite3.connect("db/bio_latam.db")

GRANT_PATTERNS = {
    "anpcyt": [r"\bANPCyT\b", r"\bFONTAR\b", r"\bFONCyT\b", r"\bANPCIT\b"],
    "finep": [r"\bFINEP\b"],
    "sebrae": [r"\bSEBRAE\b"],
    "corfo": [r"\bCORFO\b", r"Start-Up Chile", r"Startup Chile", r"CORFO"],
    "inia": [r"\bINIA\b"],
    "embrapa": [r"\bEMBRAPA\b"],
}

CORP_PATTERNS = {
    "bayer_crop": [r"\bBayer\b"],
    "basf_agricultural": [r"\bBASF\b", r"AgroStart"],
    "corteva": [r"\bCorteva\b"],
    "syngenta": [r"\bSyngenta\b"],
    "novonesis": [r"\bNovonesis\b", r"\bNovozymes\b", r"\bChr\.?\s*Hansen\b"],
    "cargill": [r"\bCargill\b"],
    "bunge": [r"\bBunge\b"],
}

# Fetch all startups with summaries
rows = conn.execute("""
    SELECT se.startup_id, e.canonical_name,
           se.startup_summary_v1, se.startup_summary_en, se.business_one_liner, se.technical_stack,
           e.country_code
    FROM startup_extended se
    JOIN entities e ON se.startup_id = e.entity_id
    WHERE se.startup_summary_v1 IS NOT NULL OR se.startup_summary_en IS NOT NULL
""").fetchall()

# Already-existing support edges
existing_support = set(
    (r[0], r[1]) for r in conn.execute(
        "SELECT source_entity_id, target_entity_id FROM support_edges WHERE support_type='grant_recipient'"
    )
)
existing_validation = set(
    (r[0], r[1]) for r in conn.execute(
        "SELECT startup_id, counterparty_entity_id FROM validation_edges"
    )
)

grant_candidates = []
corp_candidates = []

for row in rows:
    startup_id, name, summary_v1, summary_en, one_liner, tech_stack, country = row
    text = " ".join(filter(None, [summary_v1, summary_en, one_liner, tech_stack]))
    if not text:
        continue

    for entity_id, patterns in GRANT_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                key = (entity_id, startup_id)
                if key not in existing_support:
                    # Find the matched text snippet
                    match = re.search(r".{0,60}" + pat.strip(r"\b") + r".{0,60}", text, re.IGNORECASE)
                    snippet = match.group(0).strip() if match else ""
                    grant_candidates.append({
                        "entity_id": entity_id,
                        "startup_id": startup_id,
                        "name": name,
                        "country": country,
                        "pattern": pat,
                        "snippet": snippet,
                    })
                break  # one match per entity is enough

    for entity_id, patterns in CORP_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                key = (startup_id, entity_id)
                if key not in existing_validation:
                    match = re.search(r".{0,60}" + pat.strip(r"\b") + r".{0,60}", text, re.IGNORECASE)
                    snippet = match.group(0).strip() if match else ""
                    corp_candidates.append({
                        "entity_id": entity_id,
                        "startup_id": startup_id,
                        "name": name,
                        "country": country,
                        "pattern": pat,
                        "snippet": snippet,
                    })
                break

print(f"\n{'='*60}")
print(f"GRANT CANDIDATES (new grant_recipient edges): {len(grant_candidates)}")
print(f"{'='*60}")
for c in sorted(grant_candidates, key=lambda x: x["entity_id"]):
    print(f"  {c['entity_id']:20s} -> {c['startup_id']:30s} [{c['country']}]")
    if c["snippet"]:
        print(f"    snippet: ...{c['snippet']}...")

print(f"\n{'='*60}")
print(f"CORPORATE CANDIDATES (new validation_edges): {len(corp_candidates)}")
print(f"{'='*60}")
for c in sorted(corp_candidates, key=lambda x: x["entity_id"]):
    print(f"  {c['entity_id']:20s} <- {c['startup_id']:30s} [{c['country']}]")
    if c["snippet"]:
        print(f"    snippet: ...{c['snippet']}...")
