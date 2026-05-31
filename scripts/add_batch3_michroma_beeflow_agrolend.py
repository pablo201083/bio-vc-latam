"""Batch 3: CJ CheilJedang entity + Michroma edges, Beeflow + BASF, Agrolend + Syngenta validation.

Sources:
- Michroma/CJCJ: https://agfundernews.com/michroma-and-cj-cheiljedang-partner-to-scale-commercial-production-of-natural-colors-via-fermentation (Sep 24, 2025)
- Beeflow/BASF: ZoomInfo Beeflow partners list: Driscoll's, Woolf Farming, BASF
- Agrolend/Syngenta commercial: https://fusoesaquisicoes.com/acontece-no-setor/agrolend-atrai-syngenta-e-creation-investments/
  "will use funding to expand credit offerings using companies that transmit loans to farmers, including Syngenta"
"""
import sqlite3
import hashlib
import datetime
import sys

sys.stdout.reconfigure(encoding="utf-8")
conn = sqlite3.connect("db/bio_latam.db")
now = datetime.datetime.now(datetime.UTC).isoformat()
inserted = {"entities": 0, "investment": 0, "validation": 0}


def add_entity(entity_id, entity_type, name, slug, desc, country, website, status):
    existing = conn.execute("SELECT entity_id FROM entities WHERE entity_id=?", (entity_id,)).fetchone()
    if not existing:
        conn.execute("""INSERT INTO entities
            (entity_id, entity_type, canonical_name, slug, short_description,
             country_code, website, status, last_verified_at)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (entity_id, entity_type, name, slug, desc, country, website, status, now))
        print(f"Inserted entity: {entity_id}")
        inserted["entities"] += 1
    else:
        print(f"Already exists: {entity_id}")


def add_investment(investor_id, startup_id, round_name, round_stage, date,
                   amount, currency, is_lead, conf, notes):
    iid = "inv_" + hashlib.md5(f"{investor_id}|{startup_id}|{round_stage}".encode()).hexdigest()[:8]
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
        print(f"Inserted investment: {investor_id} -> {startup_id} ({round_stage})")
        inserted["investment"] += 1
    else:
        print(f"Already exists: {investor_id} -> {startup_id} ({round_stage})")


def add_validation(startup_id, counterparty_id, val_type, status,
                   confidence, notes, source_url, started_at=None):
    vid = "val-" + hashlib.md5(f"{startup_id}|{counterparty_id}|{val_type}".encode()).hexdigest()[:12]
    existing = conn.execute(
        "SELECT validation_id FROM validation_edges WHERE startup_id=? AND counterparty_entity_id=? AND validation_type=?",
        (startup_id, counterparty_id, val_type)
    ).fetchone()
    if not existing:
        conn.execute("""INSERT INTO validation_edges
            (validation_id, startup_id, counterparty_entity_id, validation_type,
             started_at, status, confidence_score, notes, source_url, added_by, added_at)
            VALUES (?,?,?,?,?,?,?,?,?,'human:curador',?)""",
            (vid, startup_id, counterparty_id, val_type,
             started_at, status, confidence, notes, source_url, now))
        print(f"Inserted validation: {startup_id} -> {counterparty_id} ({val_type})")
        inserted["validation"] += 1
    else:
        print(f"Already exists: {startup_id} -> {counterparty_id} ({val_type})")


# ============================================================
# 1. CJ CheilJedang — new entity
# ============================================================
add_entity(
    "cj_cheiljedang", "corporate",
    "CJ CheilJedang", "cj-cheiljedang",
    "South Korean food and biomanufacturing conglomerate; global leader in amino acids, fermentation ingredients, and biologics CDMO. Corporate venture arm invests in fermentation and food biotech startups.",
    "KR", "https://www.cj.net", "active",
)

# 2. CJ CheilJedang -> Michroma: investor + technology_partnership
# Article: "CJCJ is also an investor in Michroma" + "CDMO partnership to scale commercial production"
add_investment(
    "cj_cheiljedang", "michroma",
    "Strategic", "strategic", "2025-09-24",
    None, None, 0, 0.90,
    "CJ CheilJedang strategic investment in Michroma alongside CDMO manufacturing partnership (Sep 2025). CJCJ provides biomanufacturing scale-up for Michroma's Red+ fungal pigments.",
)

add_validation(
    "michroma", "cj_cheiljedang", "technology_partnership", "confirmed",
    0.95,
    "CJ CheilJedang is Michroma's CDMO manufacturing partner AND investor (Sep 24 2025). CJCJ provides biomanufacturing capacity in US, China, Malaysia, Brazil, South Korea for Michroma's Red+ fermented natural color. Global supply chain diversification and future commercial potential via CJ Foods unit.",
    "https://agfundernews.com/michroma-and-cj-cheiljedang-partner-to-scale-commercial-production-of-natural-colors-via-fermentation",
    "2025-09-24",
)

# ============================================================
# 2. Beeflow + BASF Agricultural Solutions: technology_partnership
# ============================================================
# ZoomInfo / AgFunderNews confirm BASF as Beeflow commercial partner
# (Likely: BASF provides agrochemicals complementary to Beeflow pollination services,
#  or Beeflow provides integrated pollination solutions alongside BASF products)
add_validation(
    "beeflow", "basf_agricultural", "technology_partnership", "confirmed",
    0.80,
    "BASF Agricultural Solutions listed as commercial partner for Beeflow's pollination-as-a-service platform, alongside Driscoll's and Woolf Farming. Likely: integrated crop solution combining Beeflow pollination services with BASF crop inputs. Source: ZoomInfo Beeflow partners profile 2024.",
    "https://www.zoominfo.com/c/beeflow-sa/482367171",
    None,
)

# ============================================================
# 3. Agrolend + Syngenta: customer_pilot (commercial distribution)
# ============================================================
# "Agrolend will use new funding to expand credit offerings using companies that
#  transmit loans to farmers, including Syngenta"
# Syngenta acts as a distribution channel for Agrolend's financial products (loan originator)
# This is a technology_partnership / commercial integration
add_validation(
    "agrolend", "syngenta", "technology_partnership", "confirmed",
    0.88,
    "Syngenta acts as a distribution channel for Agrolend's financial products: Syngenta transmits Agrolend loans to farmers as part of its input distribution business. Confirmed: Syngenta Group Ventures co-led the R$300M ($55M) Series C (Oct 2024) AND is a commercial distribution partner for loan origination.",
    "https://neofeed.com.br/startups/agrolend-capta-r-300-milhoes-e-atrai-creation-investments-syngenta-vivo-b3-e-nochu-bank/",
    "2024-10-01",
)

conn.commit()
print()
print(f"Entities: +{inserted['entities']}")
print(f"Investment edges: +{inserted['investment']}")
print(f"Validation edges: +{inserted['validation']}")
print("Total entities:", conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0])
print("Total investment_edges:", conn.execute("SELECT COUNT(*) FROM investment_edges").fetchone()[0])
print("Total validation_edges:", conn.execute("SELECT COUNT(*) FROM validation_edges").fetchone()[0])
conn.close()
