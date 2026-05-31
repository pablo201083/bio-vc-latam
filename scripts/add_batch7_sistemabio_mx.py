"""Batch 7: Sistema.bio investors + Earth Ocean Farms investor.

Sources:
- Sistema.bio $12M Series A: https://www.lavca.org/dila-capital-shell-foundation-endeavor-catalyst-and-others-invest-us12m-in-sistema-bio/
  DILA Capital (lead), Shell Foundation, Engie RDE Fund, EcoEnterprise Fund, Endeavor Catalyst
- Sistema.bio $15M pre-Series C (Oct 2024): https://edfimc.eu/electrifi-further-deepens-its-strategic-investment-in-sistema-bio-and-leads-crucial-internal-pre-series-c-round/
  ElectriFI/EDFI Management Company (lead); existing investors including KawiSafi, Chroma, EcoEnterprises
- Earth Ocean Farms / Cuna del Mar: https://www.cunadelmar.com/
"""
import sqlite3
import hashlib
import datetime
import sys

sys.stdout.reconfigure(encoding="utf-8")
conn = sqlite3.connect("db/bio_latam.db")
now = datetime.datetime.now(datetime.UTC).isoformat()

LAVCA_URL = "https://www.lavca.org/dila-capital-shell-foundation-endeavor-catalyst-and-others-invest-us12m-in-sistema-bio/"
EDFI_URL = "https://edfimc.eu/electrifi-further-deepens-its-strategic-investment-in-sistema-bio-and-leads-crucial-internal-pre-series-c-round/"


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
add_entity("dila_capital", "investor", "DILA Capital", "dila-capital",
           "Mexico City-based multi-stage VC firm investing in Spanish-speaking world; $260M+ AUM across 4 funds; focus on tech, fintech, healthtech; led Sistema.bio Series A.",
           "MX", "https://www.dilacapital.com", "active")

add_entity("electrifi", "investor", "ElectriFI", "electrifi",
           "European impact investment facility managed by EDFI Management Company; funded by EU, USAID Power Africa, Sweden and Italy; focuses on energy access and clean tech in emerging markets.",
           "BE", "https://edfimc.eu", "active")

add_entity("shell_foundation", "investor", "Shell Foundation", "shell-foundation",
           "UK independent charitable foundation backed by Shell; invests in access-to-energy and sustainable agriculture enterprises in developing countries; provided junior debt to Sistema.bio.",
           "GB", "https://www.shellfoundation.org", "active")

add_entity("endeavor_catalyst", "investor", "Endeavor Catalyst", "endeavor-catalyst",
           "Co-investment fund of Endeavor Global that invests in Endeavor Entrepreneur companies; provides capital alongside institutional investors to high-impact LATAM startups.",
           "US", "https://endeavor.org/catalyst", "active")

add_entity("kawisafi_ventures", "investor", "KawiSafi Ventures", "kawisafi-ventures",
           "Africa/global impact VC focused on clean energy and sustainable agriculture access; backed by Omidyar Network; investor in Sistema.bio.",
           "KE", "https://www.kawisafi.com", "active")

add_entity("cuna_del_mar", "investor", "Cuna del Mar", "cuna-del-mar",
           "US aquaculture investment fund backed by Walton family; invests in open-ocean and regenerative aquaculture companies in Americas; portfolio includes Earth Ocean Farms (Mexico).",
           "US", "https://www.cunadelmar.com", "active")

# ============================================================
# 2. Sistema.bio investment edges
# ============================================================
print()
print("=== Sistema.bio Series A ($12M, 2019) ===")
add_investment("dila_capital", "sistema-bio-mx",
               "Series A", "series-a", "2019-05-27",
               12_000_000, "USD", 1, 0.97,
               "DILA Capital LED Sistema.bio $12M Series A (May 2019) alongside Shell Foundation, Engie RDE Fund, EcoEnterprise Fund, Endeavor Catalyst, CoCapital, Triodos, Alpha Mundi, Lendahand. Sistema.bio: small-scale biodigester tech for smallholder farmers in Mexico, LATAM, Africa, India. Source: LAVCA / official release.")

add_investment("shell_foundation", "sistema-bio-mx",
               "Series A", "series-a", "2019-05-27",
               None, None, 0, 0.95,
               "Shell Foundation co-invested in Sistema.bio $12M Series A (May 2019) led by DILA Capital; also provided junior debt in 2024 bridge round. Source: LAVCA announcement.")

add_investment("endeavor_catalyst", "sistema-bio-mx",
               "Series A", "series-a", "2019-05-27",
               None, None, 0, 0.95,
               "Endeavor Catalyst co-invested in Sistema.bio $12M Series A (May 2019) led by DILA Capital. Sistema.bio founded by Endeavor Entrepreneurs Camilo Pages and Alexander Eaton. Source: Endeavor / LAVCA.")

print()
print("=== Sistema.bio pre-Series C ($15M, Oct 2024) ===")
add_investment("electrifi", "sistema-bio-mx",
               "Pre-Series C", "pre-series-c", "2024-10-14",
               15_000_000, "USD", 1, 0.97,
               "ElectriFI (EDFI Management Company) led Sistema.bio $15M pre-Series C (Oct 14, 2024); described as 'internal round' with all existing investors. Participating: Chroma Impact Investment, KawiSafi Ventures, AXA IM Alts, Blink CV, EcoEnterprises Fund; lenders FMO, Triodos; junior debt BIX Capital + Shell Foundation. Anticipating Series C in 2025. Source: EDFI MC official release.")

add_investment("kawisafi_ventures", "sistema-bio-mx",
               "Pre-Series C", "pre-series-c", "2024-10-14",
               None, None, 0, 0.95,
               "KawiSafi Ventures co-invested in Sistema.bio $15M pre-Series C (Oct 2024) as existing equity holder. Source: EDFI MC release.")

# ============================================================
# 3. Earth Ocean Farms — Cuna del Mar investor
# ============================================================
print()
print("=== Earth Ocean Farms — Cuna del Mar ===")
add_investment("cuna_del_mar", "earth-ocean-farms-mx",
               "Undisclosed", "undisclosed", None,
               None, None, 0, 0.85,
               "Cuna del Mar (Walton-backed aquaculture VC, US) is listed as investor/portfolio holder of Earth Ocean Farms (now rebranded as Santomar; La Paz, BCS, Mexico). Open-ocean regenerative marine aquaculture of Pacific red snapper and totoaba. Amount undisclosed. Source: Cuna del Mar portfolio page.")

conn.commit()
print()
print("Total entities:", conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0])
print("Total investment_edges:", conn.execute("SELECT COUNT(*) FROM investment_edges").fetchone()[0])
conn.close()
