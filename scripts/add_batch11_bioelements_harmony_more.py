"""Batch 11: BioElements/BTG Pactual Series A, Harmony Baby/BNDES+FINEP grant, more.

Sources:
- BioElements $30M Series A: https://www.globalprivatecapital.org/newsroom/btg-pactual-leads-usd30m-round-for-chiles-bioelements/
  BTG Pactual leads $30M (Jan 13, 2023) for CL bioplastics startup
- Harmony Baby Nutrition / BNDES+FINEP: https://www.foodbev.com/news/harmony-baby-nutrition-secures-5-9m-to-launch-r-d-centre-in-brazil
  R$31.8M (~$5.8M) from BNDES + FINEP (Nova Industria Brasil policy)
"""
import sqlite3
import hashlib
import datetime
import sys

sys.stdout.reconfigure(encoding="utf-8")
conn = sqlite3.connect("db/bio_latam.db")
now = datetime.datetime.now(datetime.UTC).isoformat()

BIOELEMENTS_URL = "https://www.globalprivatecapital.org/newsroom/btg-pactual-leads-usd30m-round-for-chiles-bioelements/"
HARMONY_URL = "https://www.foodbev.com/news/harmony-baby-nutrition-secures-5-9m-to-launch-r-d-centre-in-brazil"


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


# ============================================================
# 1. New entities
# ============================================================
add_entity("btg_pactual", "investor", "BTG Pactual", "btg-pactual",
           "Brazil's largest investment bank and LATAM's leading investment bank; active in VC/PE for tech and sustainability-focused LATAM startups; led BioElements CL $30M Series A.",
           "BR", "https://www.btgpactual.com", "active")

add_entity("bndes", "eso", "BNDES (Banco Nacional de Desenvolvimento)", "bndes",
           "Brazilian Development Bank; primary public funder of innovation and industrial development in Brazil; co-funds biotech/deeptech through programs like Nova Indústria Brasil alongside FINEP.",
           "BR", "https://www.bndes.gov.br", "active")

# ============================================================
# 2. BioElements — BTG Pactual Series A ($30M, Jan 2023)
# ============================================================
print()
print("=== BioElements $30M Series A (Jan 2023) ===")
add_investment("btg_pactual", "bioelements-cl",
               "Series A", "series-a", "2023-01-13",
               30_000_000, "USD", 1, 0.97,
               "BTG Pactual led BioElements $30M Series A (Jan 13, 2023). BioElements (Santiago, CL): biodegradable bioplastic packaging (resins decompose in 6 months); operations in 7 countries (CL, PE, CO, AR, BR, MX, US). Funds used for regional expansion + R&D. Source: GPCA / ImpactAlpha / Bloomberg Linea.")

# ============================================================
# 3. Harmony Baby Nutrition — BNDES + FINEP grant (2025)
# ============================================================
# harmony-biosciences is the correct entity_id for Harmony Baby Nutrition BR
print()
print("=== Harmony Baby Nutrition / BNDES + FINEP grant ===")
add_support("bndes", "harmony-biosciences", "grant_recipient", 0.95,
            "BNDES co-awarded R$31.8M (~$5.8M) to Harmony Baby Nutrition (Belo Horizonte, BR) under Nova Indústria Brasil policy to establish R&D centre for precision fermentation of human milk proteins (lactoferrin, alpha-lactalbumin). R&D centre to open H1 2026. Source: FoodBev / GreenQueen / official.",
            HARMONY_URL)

add_support("finep", "harmony-biosciences", "grant_recipient", 0.95,
            "FINEP co-awarded R$31.8M (~$5.8M) to Harmony Baby Nutrition (BR) under Nova Indústria Brasil policy, jointly with BNDES. Grant supports precision fermentation R&D for breastmilk-inspired infant formula ingredients. Source: FoodBev / Femtech Insider.",
            HARMONY_URL)

# ============================================================
# 4. BioElements CL — CORFO support (GoGlobal program)
# ============================================================
add_support("corfo", "bioelements-cl", "accelerator_cohort", 0.82,
            "BioElements was selected as one of 39 companies in CORFO + ProChile GoGlobal export acceleration program. Source: company profile / CORFO listing.",
            "https://impactalpha.com/bioelements-secures-30-million-for-bioplastics-in-latin-america/")

conn.commit()
print()
print("Total entities:", conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0])
print("Total investment_edges:", conn.execute("SELECT COUNT(*) FROM investment_edges").fetchone()[0])
print("Total support_edges:", conn.execute("SELECT COUNT(*) FROM support_edges").fetchone()[0])
conn.close()
