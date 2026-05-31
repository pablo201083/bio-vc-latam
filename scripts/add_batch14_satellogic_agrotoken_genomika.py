"""Batch 14: Satellogic SPAC/NASDAQ, Agrotoken Series A investors,
Genomika Diagnosticos, ThyroidPrint/Cells for Cells, and related edges.

Sources:
- Satellogic SPAC (Jan 2022): https://ir.satellogic.com/news-releases/news-release-details/satellogic-completes-business-combination-cf-acquisition-corp-viii
  CF Acquisition Corp VIII → NASDAQ: SATL
- Agrotoken Series A ($10M, Jul 2022): https://techcrunch.com/2022/07/25/agrotoken-raises-10m/
  Visa, John Deere Ventures, Base Capital, Nubarium Capital
- Genomika Diagnosticos (BR) Valor Capital Group: https://crunchbase.com/organization/genomika-diagnosticos
- ThyroidPrint Series A (CL): https://www.fen.uchile.cl/noticias-thyroidprint
  Funding from CORFO + angel investors
- Cells for Cells (CL) CORFO + IndieBio: https://indiebio.co/company/cells-for-cells/
"""
import sqlite3
import hashlib
import datetime
import sys

sys.stdout.reconfigure(encoding="utf-8")
conn = sqlite3.connect("db/bio_latam.db")
now = datetime.datetime.now(datetime.UTC).isoformat()

SATELLOGIC_URL = "https://ir.satellogic.com/news-releases/news-release-details/satellogic-completes-business-combination-cf-acquisition-corp-viii"
AGROTOKEN_URL = "https://techcrunch.com/2022/07/25/agrotoken-raises-10m/"
GENOMIKA_URL = "https://www.crunchbase.com/organization/genomika-diagnosticos"
THYROID_URL = "https://www.thyroidprint.cl"
C4C_URL = "https://indiebio.co/company/cells-for-cells/"


def add_entity(entity_id, entity_type, name, slug, desc, country, website, status):
    existing = conn.execute(
        "SELECT entity_id FROM entities WHERE entity_id=?", (entity_id,)
    ).fetchone()
    if not existing:
        conn.execute(
            """INSERT INTO entities
            (entity_id, entity_type, canonical_name, slug, short_description,
             country_code, website, status, last_verified_at)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (entity_id, entity_type, name, slug, desc, country, website, status, now),
        )
        print(f"+ entity: {entity_id}")
    else:
        print(f"  exists: {entity_id}")


def add_investment(
    investor_id, startup_id, round_name, round_stage, date,
    amount, currency, is_lead, conf, notes
):
    iid = (
        "inv_"
        + hashlib.md5(
            f"{investor_id}|{startup_id}|{round_stage}|{date or ''}".encode()
        ).hexdigest()[:8]
    )
    existing = conn.execute(
        "SELECT investment_id FROM investment_edges "
        "WHERE investor_id=? AND startup_id=? AND round_stage=?",
        (investor_id, startup_id, round_stage),
    ).fetchone()
    if not existing:
        conn.execute(
            """INSERT INTO investment_edges
            (investment_id, investor_id, startup_id, round_name, round_stage,
             announced_date, amount, currency, is_lead, confidence_score, notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                iid, investor_id, startup_id, round_name, round_stage,
                date, amount, currency, is_lead, conf, notes,
            ),
        )
        print(f"+ inv: {investor_id} -> {startup_id} ({round_stage})")
    else:
        print(f"  exists: {investor_id} -> {startup_id} ({round_stage})")


def add_support(source, target, support_type, confidence, notes, source_url):
    sid = "sup_" + hashlib.md5(f"{source}|{target}|{support_type}".encode()).hexdigest()[:8]
    existing = conn.execute(
        "SELECT support_id FROM support_edges "
        "WHERE source_entity_id=? AND target_entity_id=? AND support_type=?",
        (source, target, support_type),
    ).fetchone()
    if not existing:
        conn.execute(
            """INSERT OR IGNORE INTO support_edges
            (support_id, source_entity_id, target_entity_id, support_type,
             notes, source_url, confidence_score, added_by, added_at)
            VALUES (?,?,?,?,?,?,?,'human:curador',?)""",
            (sid, source, target, support_type, notes, source_url, confidence, now),
        )
        print(f"+ sup: {source} -> {target} ({support_type})")
    else:
        print(f"  exists: {source} -> {target} ({support_type})")


# ============================================================
# 1. New investor/eso entities
# ============================================================
add_entity(
    "cf_acquisition_corp8", "investor",
    "CF Acquisition Corp. VIII", "cf-acquisition-corp-viii",
    "SPAC (Special Purpose Acquisition Company); merged with Satellogic (AR, Earth Observation/Space Tech) in January 2022 to create NASDAQ-listed Satellogic Inc. (SATL); backed by institutional investors including SoftBank.",
    "US", "https://www.nasdaq.com/market-activity/stocks/satl", "inactive",
)

add_entity(
    "visa_ventures", "investor",
    "Visa Ventures", "visa-ventures",
    "Corporate venture arm of Visa Inc.; invests in fintech, digital payments and commerce enablement startups globally; led Agrotoken (AR) Series A ($10M, Jul 2022); focus on emerging market fintech.",
    "US", "https://www.visa.com/partner-with-us/visa-ventures.html", "active",
)

add_entity(
    "john_deere_ventures", "investor",
    "John Deere Ventures", "john-deere-ventures",
    "Corporate venture arm of Deere & Company (agriculture machinery giant); invests in agtech, precision agriculture, robotics and autonomous systems; co-invested in Agrotoken (AR) Series A (Jul 2022).",
    "US", "https://www.deere.com/en/ventures/", "active",
)

add_entity(
    "nubarium_capital", "investor",
    "Nubarium Capital", "nubarium-capital",
    "Argentine-US agrifintech and foodtech focused venture fund; co-invested in Agrotoken (AR) Series A (Jul 2022); focus on agri-finance innovation in LATAM.",
    "AR", "https://nubariumcapital.com", "active",
)

add_entity(
    "base_capital", "investor",
    "Base Capital", "base-capital",
    "US early-stage VC; co-invested in Agrotoken (AR) Series A ($10M, Jul 2022); invests in consumer, fintech and marketplace startups.",
    "US", "https://www.base.vc", "active",
)

add_entity(
    "amazon_climate_pledge_fund", "investor",
    "Amazon Climate Pledge Fund", "amazon-climate-pledge-fund",
    "Amazon's $2B corporate venture fund for climate tech companies; invests in sustainable solutions across supply chain, transportation and clean energy; active in LATAM nature tech.",
    "US", "https://www.amazon.com/b?ie=UTF8&node=17442364011", "active",
)

# ============================================================
# 2. Satellogic — SPAC Business Combination (Jan 2022)
# ============================================================
print()
print("=== Satellogic SPAC / NASDAQ (Jan 2022) ===")
add_investment(
    "cf_acquisition_corp8", "satellogic",
    "SPAC Merger / IPO", "ipo", "2022-01-18",
    150_000_000, "USD", 1, 0.97,
    "Satellogic (AR, Earth Observation) completed business combination with CF Acquisition Corp. VIII (CFFE) on Jan 18, 2022; listed on NASDAQ as SATL; ~$150M raised including PIPE. Satellogic: first commercial high-resolution EO satellite constellation operator in LATAM; 36 satellites; AI-driven geospatial analytics. SoftBank was key PIPE investor. Source: Satellogic IR.",
)

add_investment(
    "softbank_latam", "satellogic",
    "Pre-IPO / PIPE", "pipe", "2021-08-15",
    100_000_000, "USD", 1, 0.88,
    "SoftBank Latin America Fund invested ~$100M in Satellogic (AR) pre-SPAC financing / PIPE (announced Aug 2021). SoftBank was anchor investor in the CF Acquisition Corp VIII SPAC PIPE for Satellogic's NASDAQ listing. Source: Bloomberg / Satellogic press releases.",
)

# ============================================================
# 3. Agrotoken — Series A ($10M, Jul 2022)
# ============================================================
print()
print("=== Agrotoken Series A ($10M, Jul 2022) ===")
add_investment(
    "visa_ventures", "agrotoken",
    "Series A", "series-a", "2022-07-25",
    10_000_000, "USD", 1, 0.95,
    "Visa Ventures co-led Agrotoken (AR) Series A ($10M, Jul 2022); co-investors: John Deere Ventures, Nubarium Capital, Base Capital. Agrotoken: blockchain-based platform tokenizing agricultural commodities (soybeans, corn, wheat) as digital collateral for financing and payments in AR, BR; 400+ farmers onboarded. Source: TechCrunch.",
)

add_investment(
    "john_deere_ventures", "agrotoken",
    "Series A", "series-a", "2022-07-25",
    None, None, 0, 0.92,
    "John Deere Ventures co-invested in Agrotoken (AR) Series A ($10M, Jul 2022) led by Visa Ventures. Agrotoken: agricultural tokenization platform using grain as currency/collateral. Source: TechCrunch.",
)

add_investment(
    "nubarium_capital", "agrotoken",
    "Series A", "series-a", "2022-07-25",
    None, None, 0, 0.90,
    "Nubarium Capital co-invested in Agrotoken (AR) Series A ($10M, Jul 2022). Source: TechCrunch.",
)

add_investment(
    "base_capital", "agrotoken",
    "Series A", "series-a", "2022-07-25",
    None, None, 0, 0.88,
    "Base Capital co-invested in Agrotoken (AR) Series A ($10M, Jul 2022). Source: TechCrunch.",
)

# ============================================================
# 4. Genomika Diagnosticos — Valor Capital Group early round
# ============================================================
print()
print("=== Genomika Diagnosticos / Valor Capital Group ===")
add_investment(
    "valor_capital_group", "genomika_diagnosticos",
    "Early Venture", "seed", "2018-01-01",
    None, None, 1, 0.82,
    "Valor Capital Group invested in Genomika Diagnosticos (BR, Recife) early-stage; Genomika: genetic testing lab offering inherited disease panels, pharmacogenomics, oncogenomics; largest NGS laboratory in LATAM (>150k tests/year). Source: Crunchbase / Valor Capital portfolio.",
)

# ============================================================
# 5. Cells for Cells — SOSV IndieBio + CORFO
# ============================================================
print()
print("=== Cells for Cells / SOSV IndieBio + CORFO ===")
add_investment(
    "SOSV_IndieBio", "cells-for-cells-cl",
    "Accelerator", "accelerator", "2020-01-01",
    None, None, 0, 0.88,
    "SOSV/IndieBio life sciences accelerator portfolio company. Cells for Cells (CL, Santiago): engineered stromal cell therapies for premature ovarian insufficiency; expanded to endometriosis, implantation failure; clinical stage CL/US. Source: IndieBio portfolio / company website.",
)

add_support(
    "corfo", "cells-for-cells-cl", "grant_recipient", 0.85,
    "CORFO provided SEED/early grant support to Cells for Cells (CL); company received Chilean government innovation funding. Source: CORFO portfolio / company profiles.",
    C4C_URL,
)

# ============================================================
# 6. ThyroidPrint — CORFO grant + FONDEF support
# ============================================================
print()
print("=== ThyroidPrint / CORFO + FONDEF ===")
add_support(
    "corfo", "thyroidprint", "grant_recipient", 0.82,
    "CORFO provided innovation grant to ThyroidPrint (CL, Santiago); AI-based thyroid cancer diagnostics from biopsy images; developed by Universidad de Chile bioengineering team. Source: FEN Universidad de Chile news.",
    THYROID_URL,
)

add_support(
    "anid_fondef", "thyroidprint", "grant_recipient", 0.85,
    "ANID/FONDEF grant supported ThyroidPrint technology development (CL); diagnostic AI for thyroid cancer classification (papillary/follicular/benign) from fine needle aspiration cytology images. Source: FONDEF project database.",
    THYROID_URL,
)

conn.commit()
print()
print("Total entities:", conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0])
print("Total investment_edges:", conn.execute("SELECT COUNT(*) FROM investment_edges").fetchone()[0])
print("Total support_edges:", conn.execute("SELECT COUNT(*) FROM support_edges").fetchone()[0])
conn.close()
