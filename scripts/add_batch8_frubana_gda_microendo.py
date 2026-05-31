"""Batch 8: Frubana Series B investors, Grupo Diagnostico Aries/CDPQ, MicroEndo/SOSV.

Sources:
- Frubana Series B ($65M, Jun 2021): https://www.lavca.org/ggv-leads-usd65m-series-b-in-colombian-restaurant-and-retail-platform-frubana/
  GGV Capital (lead), Lightspeed Venture Partners, SoftBank, Tiger Global, Monashees
- Grupo Diagnostico Aries / CDPQ: https://www.prnewswire.com/news-releases/cdpq-invests-in-grupo-diagnostico-aries-301402158.html
  CDPQ acquired 20.25% minority stake (Oct 18, 2021)
- MicroEndo / SOSV RebelBio: https://sosv.com/company/microendo/
"""
import sqlite3
import hashlib
import datetime
import sys

sys.stdout.reconfigure(encoding="utf-8")
conn = sqlite3.connect("db/bio_latam.db")
now = datetime.datetime.now(datetime.UTC).isoformat()

FRUBANA_URL = "https://www.lavca.org/ggv-leads-usd65m-series-b-in-colombian-restaurant-and-retail-platform-frubana/"
GDA_URL = "https://www.prnewswire.com/news-releases/cdpq-invests-in-grupo-diagnostico-aries-301402158.html"
MICROENDO_URL = "https://sosv.com/company/microendo/"


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
# 1. New investor entities
# ============================================================
add_entity("ggv_capital", "investor", "GGV Capital", "ggv-capital",
           "Global multi-stage VC with offices in US and Asia; invests in consumer, enterprise, and marketplace startups; led Frubana $65M Series B in LATAM.",
           "US", "https://www.ggvc.com", "active")

add_entity("tiger_global", "investor", "Tiger Global Management", "tiger-global",
           "Global technology-focused hedge fund and VC based in NYC; invests in internet, software and fintech globally including LATAM; co-invested in Frubana Series B.",
           "US", "https://www.tigerglobal.com", "active")

add_entity("lightspeed_vp", "investor", "Lightspeed Venture Partners", "lightspeed-vp",
           "US multi-stage VC based in Menlo Park; invests in enterprise, consumer, and fintech startups globally; co-invested in Frubana Series B.",
           "US", "https://lsvp.com", "active")

add_entity("softbank_latam", "investor", "SoftBank Latin America Fund", "softbank-latam",
           "SoftBank's dedicated $8B+ VC fund for Latin American tech startups; one of largest LATAM tech investors; backed Frubana, iFood, Rappi and others.",
           "US", "https://www.softbank.com/en/investment/laf", "active")

add_entity("cdpq", "investor", "CDPQ (Caisse de dépôt)", "cdpq",
           "Canadian institutional investor (Quebec pension plan, CAD 400B+ AUM); invests in private equity and infrastructure globally; acquired 20.25% of Grupo Diagnóstico Aries (2021).",
           "CA", "https://www.cdpq.com", "active")

# ============================================================
# 2. Frubana Series B ($65M, Jun 2021)
# ============================================================
print()
print("=== Frubana Series B ($65M, Jun 2021) ===")
add_investment("ggv_capital", "frubana",
               "Series B", "series-b", "2021-06-01",
               65_000_000, "USD", 1, 0.97,
               "GGV Capital (Hans Tung) led Frubana $65M Series B (Jun 2021) alongside Lightspeed, SoftBank, Tiger Global, Monashees. Frubana: B2B food marketplace connecting smallholder farmers to restaurants/retailers in Colombia, Mexico, Brazil. Source: LAVCA / FinanceColombia.")

add_investment("lightspeed_vp", "frubana",
               "Series B", "series-b", "2021-06-01",
               None, None, 0, 0.95,
               "Lightspeed Venture Partners co-invested in Frubana $65M Series B (Jun 2021) led by GGV Capital. Source: LAVCA.")

add_investment("softbank_latam", "frubana",
               "Series B", "series-b", "2021-06-01",
               None, None, 0, 0.95,
               "SoftBank Latin America Fund co-invested in Frubana $65M Series B (Jun 2021) led by GGV Capital. Source: LAVCA.")

add_investment("tiger_global", "frubana",
               "Series B", "series-b", "2021-06-01",
               None, None, 0, 0.95,
               "Tiger Global Management co-invested in Frubana $65M Series B (Jun 2021) led by GGV Capital. Source: LAVCA.")

add_investment("monashees", "frubana",
               "Series B", "series-b", "2021-06-01",
               None, None, 0, 0.95,
               "Monashees co-invested in Frubana $65M Series B (Jun 2021) led by GGV Capital. Monashees: major Brazilian VC with Colombia footprint. Source: LAVCA.")

# ============================================================
# 3. Grupo Diagnóstico Aries — CDPQ minority stake (Oct 2021)
# ============================================================
print()
print("=== Grupo Diagnostico Aries / CDPQ ===")
add_investment("cdpq", "grupo_diagnostico_aries",
               "Private Equity", "private-equity", "2021-10-18",
               None, None, 1, 0.95,
               "CDPQ (Quebec pension fund) acquired 20.25% minority stake in Grupo Diagnóstico Aries (Oct 18, 2021). GDA: 249 clinical lab locations across 9 Mexican states; 3 blood banks. Investment to fund organic growth + strategic acquisitions + digitalization. Amount undisclosed. Source: CDPQ / PRNewswire official release.")

# ============================================================
# 4. MicroEndo — SOSV (RebelBio accelerator)
# ============================================================
print()
print("=== MicroEndo / SOSV RebelBio ===")
add_investment("sosv", "microendo",
               "Accelerator", "accelerator", "2021-01-01",
               None, None, 0, 0.85,
               "SOSV (via RebelBio life sciences accelerator) invested in MicroEndo (Jalisco, MX). MicroEndo: personalized endophyte biofertilizers for agave, corn; 'AgaveProtect' product. Listed on SOSV portfolio page. Date approximate (2021). Source: SOSV / RebelBio portfolio.")

conn.commit()
print()
print("Total entities:", conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0])
print("Total investment_edges:", conn.execute("SELECT COUNT(*) FROM investment_edges").fetchone()[0])
conn.close()
