"""Batch 12: Copptech investors, Welli Series A, and additional edges.

Sources:
- Copptech $9.5M: https://www.aurus.cl/en/portfolio/copptech/ + IDB project page
  Aurus Capital (via Aurus Ventures III), IDB Lab co-investor; Series A Oct 2022
- Welli Series A ($8M, Jun 2025): https://costanoa.vc/backing-the-future-of-healthcare-banking-in-latin-america/
  Costanoa Ventures (lead), Animo VC, Crestone VC
"""
import sqlite3
import hashlib
import datetime
import sys

sys.stdout.reconfigure(encoding="utf-8")
conn = sqlite3.connect("db/bio_latam.db")
now = datetime.datetime.now(datetime.UTC).isoformat()

COPPTECH_URL = "https://www.aurus.cl/en/portfolio/copptech/"
WELLI_URL = "https://costanoa.vc/backing-the-future-of-healthcare-banking-in-latin-america/"


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


# ============================================================
# 1. New investor entities
# ============================================================
add_entity("aurus_capital", "investor", "Aurus Capital", "aurus-capital",
           "Chilean PE/VC fund manager; manages Aurus Ventures III (innovation around copper/mining industries) backed by IDB; portfolio includes Copptech CL.",
           "CL", "https://www.aurus.cl", "active")

add_entity("costanoa_ventures", "investor", "Costanoa Ventures", "costanoa-ventures",
           "US early-stage VC based in Palo Alto; invests in enterprise software, fintech and healthtech; led Welli (CO) Series A (Jun 2025).",
           "US", "https://costanoa.vc", "active")

add_entity("animo_vc", "investor", "Animo VC", "animo-vc",
           "Early-stage VC focused on Latin American startups; co-invested in Welli (CO) Series A (Jun 2025).",
           "US", "https://animo.vc", "active")

add_entity("crestone_vc", "investor", "Crestone VC", "crestone-vc",
           "Impact-focused early-stage VC; co-invested in Welli (CO) Series A (Jun 2025).",
           "US", "https://crestonevc.com", "active")

# ============================================================
# 2. Copptech investors (Series A, Oct 2022, $9.5M)
# ============================================================
print()
print("=== Copptech Series A ($9.5M, Oct 2022) ===")
add_investment("aurus_capital", "copptech",
               "Series A", "series-a", "2022-10-07",
               9_500_000, "USD", 1, 0.92,
               "Aurus Capital (via Aurus Ventures III fund, co-funded by IDB) led/participated in Copptech $9.5M Series A (Oct 2022). Copptech: Chilean antimicrobial technology for plastics, textiles, paints, wood; 30+ formulations. Source: Aurus Capital portfolio / IDB project page.")

add_investment("idb_lab", "copptech",
               "Series A", "series-a", "2022-10-07",
               None, None, 0, 0.88,
               "IDB Lab co-invested in Copptech (CL) as part of the IDB/Aurus Ventures III fund for copper & mining innovation. Copptech: antimicrobial nano-materials technology. Source: IDB project CH-Q0007.")

# ============================================================
# 3. Welli Series A ($8M, Jun 2025)
# ============================================================
print()
print("=== Welli Series A ($8M, Jun 2025) ===")
add_investment("costanoa_ventures", "welli-co",
               "Series A", "series-a", "2025-06-01",
               8_000_000, "USD", 1, 0.92,
               "Costanoa Ventures led Welli (CO) Series A (Jun 2025, ~$8M); co-investors Animo VC and Crestone VC. Welli: point-of-care patient financing platform for dental, fertility, aesthetic clinics in Colombia. Healthcare fintech enabling 40% increase in procedures at partner clinics. Source: Costanoa Ventures blog.")

add_investment("animo_vc", "welli-co",
               "Series A", "series-a", "2025-06-01",
               None, None, 0, 0.90,
               "Animo VC co-invested in Welli (CO) Series A (Jun 2025) led by Costanoa Ventures.")

add_investment("crestone_vc", "welli-co",
               "Series A", "series-a", "2025-06-01",
               None, None, 0, 0.90,
               "Crestone VC co-invested in Welli (CO) Series A (Jun 2025) led by Costanoa Ventures.")

conn.commit()
print()
print("Total entities:", conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0])
print("Total investment_edges:", conn.execute("SELECT COUNT(*) FROM investment_edges").fetchone()[0])
conn.close()
