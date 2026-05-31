"""Batch 10: Bio Insumos Nativa/Sumitomo acquisition, Atacama Biomaterials seed,
Giraffe Bio/SOSV, and related edges.

Sources:
- Bio Insumos Nativa + Sumitomo: https://www.sumitomocorp.com/en/jp/news/topics/2024/group/20240418_2
  Sumitomo acquired stake via Summit Agro South America (Aug 2024); CL's largest biocontrol maker (30% market share)
- Atacama Biomaterials $2.46M seed (Apr 2025): https://www.crunchbase.com/organization/atacama-biomaterials
  Investors: Claritas Capital, Front Row Fund
- Giraffe Bio + SOSV IndieBio: https://indiebio.co/company/giraffe-bio/
"""
import sqlite3
import hashlib
import datetime
import sys

sys.stdout.reconfigure(encoding="utf-8")
conn = sqlite3.connect("db/bio_latam.db")
now = datetime.datetime.now(datetime.UTC).isoformat()

BIN_URL = "https://www.sumitomocorp.com/en/jp/news/topics/2024/group/20240418_2"
ATACAMA_URL = "https://www.crunchbase.com/organization/atacama-biomaterials"
GIRAFFE_URL = "https://indiebio.co/company/giraffe-bio/"


def add_entity(entity_id, entity_type, name, slug, desc, country, website, status):
    existing = conn.execute("SELECT entity_id FROM entities WHERE entity_id=?", (entity_id,)).fetchone()
    if not existing:
        conn.execute("""INSERT INTO entities
            (entity_id, entity_type, canonical_name, slug, short_description,
             country_code, website, status, last_verified_at)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (entity_id, entity_type, name, slug, desc, country, website, status, now))
        print(f"+ entity: {entity_id}")
    else:
        print(f"  exists: {entity_id}")


def add_investment(investor_id, startup_id, round_name, round_stage, date,
                   amount, currency, is_lead, conf, notes):
    iid = "inv_" + hashlib.md5(f"{investor_id}|{startup_id}|{round_stage}|{date or ''}".encode()).hexdigest()[:8]
    existing = conn.execute(
        "SELECT investment_id FROM investment_edges WHERE investor_id=? AND startup_id=? AND round_stage=?",
        (investor_id, startup_id, round_stage)
    ).fetchone()
    if not existing:
        conn.execute("""INSERT INTO investment_edges
            (investment_id, investor_id, startup_id, round_name, round_stage,
             announced_date, amount, currency, is_lead, confidence_score, notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (iid, investor_id, startup_id, round_name, round_stage,
             date, amount, currency, is_lead, conf, notes))
        print(f"+ inv: {investor_id} -> {startup_id} ({round_stage})")
    else:
        print(f"  exists: {investor_id} -> {startup_id} ({round_stage})")


def add_support(source, target, support_type, confidence, notes, source_url):
    sid = "sup_" + hashlib.md5(f"{source}|{target}|{support_type}".encode()).hexdigest()[:8]
    existing = conn.execute(
        "SELECT support_id FROM support_edges WHERE source_entity_id=? AND target_entity_id=? AND support_type=?",
        (source, target, support_type)
    ).fetchone()
    if not existing:
        conn.execute("""INSERT OR IGNORE INTO support_edges
            (support_id, source_entity_id, target_entity_id, support_type,
             notes, source_url, confidence_score, added_by, added_at)
            VALUES (?,?,?,?,?,?,?,'human:curador',?)""",
            (sid, source, target, support_type, notes, source_url, confidence, now))
        print(f"+ sup: {source} -> {target} ({support_type})")
    else:
        print(f"  exists: {source} -> {target} ({support_type})")


def add_outcome(entity_id, outcome_type, outcome_date, counterparty_id, notes, source_url):
    conn.execute("""INSERT INTO outcomes
        (entity_id, outcome_type, outcome_date, counterparty_id, source_url, notes, added_by, added_at)
        VALUES (?,?,?,?,?,?,'human:curador',?)""",
        (entity_id, outcome_type, outcome_date, counterparty_id, source_url, notes, now))
    print(f"+ outcome: {entity_id} ({outcome_type})")


# ============================================================
# 1. New entities
# ============================================================
add_entity("sumitomo_corp", "corporate", "Sumitomo Corporation", "sumitomo-corporation",
           "Japanese trading conglomerate (Fortune Global 500); through Summit Agro South America acquired stake in Bio Insumos Nativa (Chile's largest biocontrol company) in 2024 to expand its agri-biological value chain.",
           "JP", "https://www.sumitomocorp.com", "active")

add_entity("claritas_capital", "investor", "Claritas Capital", "claritas-capital",
           "Nashville, TN-based alternative investment firm with $1B+ deployed; invested in Atacama Biomaterials CL $2.46M seed (Apr 2025).",
           "US", "https://www.claritascapital.com", "active")

add_entity("front_row_fund", "investor", "Front Row Fund", "front-row-fund",
           "Early-stage impact venture fund; co-invested in Atacama Biomaterials CL $2.46M seed round (Apr 2025).",
           "US", "https://www.frontrowfund.com", "active")

add_entity("startup_chile", "eso", "Start-Up Chile", "startup-chile",
           "CORFO-backed Chilean government accelerator program; one of largest accelerators in LATAM; provides equity-free funding + mentorship to early-stage global startups in Chile.",
           "CL", "https://www.startupchile.org", "active")

# ============================================================
# 2. Bio Insumos Nativa — Sumitomo acquisition (Aug 2024)
# ============================================================
print()
print("=== Bio Insumos Nativa / Sumitomo ===")
add_investment("sumitomo_corp", "bio-insumos-nativa-cl",
               "Strategic Acquisition", "acquisition", "2024-08-02",
               None, None, 1, 0.97,
               "Sumitomo Corporation (via subsidiary Summit Agro South America) acquired stake in Bio Insumos Nativa (CL) on Aug 2, 2024. BIN: Chile's largest biocontrol manufacturer (30% market share); biopesticides, biostimulants sold in 11 countries. Sumitomo integrates BIN into its agri-biological distribution value chain for South America. Source: Sumitomo Corp official news / Indian Chemical News.")

# Add outcome for BIN
existing_outcome = conn.execute(
    "SELECT outcome_id FROM outcomes WHERE entity_id=? AND outcome_type=?",
    ("bio-insumos-nativa-cl", "acquisition")
).fetchone()
if not existing_outcome:
    add_outcome(
        "bio-insumos-nativa-cl", "acquisition", "2024-08-02", "sumitomo_corp",
        "Bio Insumos Nativa (CL) acquired by Sumitomo Corporation via Summit Agro South America (Aug 2024). Chile's largest biocontrol company (30% domestic market share); sold to enable global distribution via Sumitomo's agribusiness network. Amount undisclosed.",
        BIN_URL
    )
else:
    print("  outcome already exists: bio-insumos-nativa-cl acquisition")

# ============================================================
# 3. Atacama Biomaterials — $2.46M Seed (Apr 2025)
# ============================================================
print()
print("=== Atacama Biomaterials $2.46M Seed ===")
add_investment("claritas_capital", "atacama-biomaterials-cl",
               "Seed", "seed", "2025-04-28",
               2_460_000, "USD", 1, 0.92,
               "Claritas Capital co-led Atacama Biomaterials $2.46M seed round (Apr 28, 2025) with Front Row Fund. Atacama: compostable wood-fiber film 'Woodpack' replacing single-use plastic packaging; founded 2019 by Chilean founders from MIT; winner South Summit Brazil 2024. Source: Crunchbase / Tracxn.")

add_investment("front_row_fund", "atacama-biomaterials-cl",
               "Seed", "seed", "2025-04-28",
               None, None, 0, 0.90,
               "Front Row Fund co-invested in Atacama Biomaterials $2.46M seed round (Apr 28, 2025). Source: Crunchbase.")

# ============================================================
# 4. Giraffe Bio — SOSV / IndieBio + Start-Up Chile
# ============================================================
print()
print("=== Giraffe Bio / SOSV + Start-Up Chile ===")
add_investment("sosv", "giraffe-bio-ar",
               "Accelerator", "accelerator", "2024-01-01",
               None, None, 0, 0.88,
               "SOSV (IndieBio life sciences accelerator) portfolio company; $1.1M raised. Giraffe Bio: cell-free biomolecules for metal extraction from low-grade ores and tailings (copper +20% recovery, lithium extraction hours vs. months). Founded 2024, Buenos Aires AR. Source: IndieBio portfolio.")

add_support("startup_chile", "giraffe-bio-ar", "accelerator_cohort", 0.85,
            "Giraffe Bio listed as Start-Up Chile portfolio/cohort participant. Source: Crunchbase / startup profiles.",
            GIRAFFE_URL)

conn.commit()
print()
print("Total entities:", conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0])
print("Total investment_edges:", conn.execute("SELECT COUNT(*) FROM investment_edges").fetchone()[0])
print("Total outcomes:", conn.execute("SELECT COUNT(*) FROM outcomes").fetchone()[0])
print("Total support_edges:", conn.execute("SELECT COUNT(*) FROM support_edges").fetchone()[0])
conn.close()
