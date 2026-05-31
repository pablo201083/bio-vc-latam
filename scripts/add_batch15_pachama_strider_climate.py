"""Batch 15: Pachama (BR nature tech), Strider SP Ventures edge,
climate/nature tech investor entities, and additional edges.

Sources:
- Pachama Series A ($15M, Dec 2020): https://techcrunch.com/2020/12/16/amazon-backed-pachama-raises-15m-for-its-forest-carbon-platform/
  Amazon Climate Pledge Fund (lead), Salesforce Ventures, Future Shape, Social Capital
- Pachama Series B ($55M, Jun 2022): https://techcrunch.com/2022/06/16/pachama-55-million-series-b-google-softbank/
  GV/Google Ventures (lead), SoftBank Latin America Fund, Amazon Climate Pledge Fund
- Strider (BR) / SP Ventures: https://sp.ventures/portfolio
  SP Ventures has Strider in confirmed portfolio
- EcoSea (CL) / IDB Lab + CORFO: https://idblab.org/investment/ecosea/
  IDB Lab invested in EcoSea aquaculture Series A
- Copper3D (CL) / CORFO + MIT Enterprise Forum: announced 2019-2021
"""
import sqlite3
import hashlib
import datetime
import sys

sys.stdout.reconfigure(encoding="utf-8")
conn = sqlite3.connect("db/bio_latam.db")
now = datetime.datetime.now(datetime.UTC).isoformat()

PACHAMA_A = "https://techcrunch.com/2020/12/16/amazon-backed-pachama-raises-15m-for-its-forest-carbon-platform/"
PACHAMA_B = "https://techcrunch.com/2022/06/16/pachama-55-million-series-b-google-softbank/"
STRIDER_URL = "https://sp.ventures/portfolio"
ECOSEA_URL = "https://idblab.org/investment/ecosea/"
COPPER3D_URL = "https://www.copper3d.com"


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
    sid = "sup_" + hashlib.md5(
        f"{source}|{target}|{support_type}".encode()
    ).hexdigest()[:8]
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
# 1. New investor entities (climate / nature tech focused)
# ============================================================
add_entity(
    "gv_google_ventures", "investor",
    "GV (Google Ventures)", "gv-google-ventures",
    "Alphabet/Google's independent venture capital arm; invests across life sciences, health, enterprise software, and deep tech; led Pachama (BR) Series B ($55M, Jun 2022); active in climate tech globally.",
    "US", "https://www.gv.com", "active",
)

add_entity(
    "salesforce_ventures", "investor",
    "Salesforce Ventures", "salesforce-ventures",
    "Corporate venture arm of Salesforce Inc. (CRM); invests in enterprise cloud software, AI, and climate/sustainability tech; co-invested in Pachama (BR) Series A ($15M, Dec 2020); partner in Salesforce.org sustainability programs.",
    "US", "https://www.salesforce.com/ventures/", "active",
)

add_entity(
    "future_shape", "investor",
    "Future Shape", "future-shape",
    "Personal investment vehicle of Tony Fadell (inventor of iPod, co-inventor of iPhone, founder of Nest); invests in transformative hardware, climate and deep tech; co-invested in Pachama (BR) Series A (Dec 2020).",
    "US", "https://www.futureshape.vc", "active",
)

add_entity(
    "social_capital", "investor",
    "Social Capital", "social-capital",
    "US venture capital firm led by Chamath Palihapitiya; invests in science, technology and healthcare; co-invested in Pachama (BR) Series A (Dec 2020); known for SPAC deals and contrarian investment thesis.",
    "US", "https://www.socialcapital.com", "active",
)

# Pachama startup entity
add_entity(
    "pachama", "startup",
    "Pachama", "pachama",
    "Brazilian-founded forest carbon verification and marketplace platform; uses satellite imagery, AI and remote sensing to verify and monitor nature-based carbon projects; enables corporates to buy verified forest carbon credits; operations across LATAM and globally.",
    "BR", "https://pachama.com", "active",
)

# ============================================================
# 2. Pachama — Series A ($15M, Dec 2020)
# ============================================================
print()
print("=== Pachama Series A ($15M, Dec 2020) ===")
add_investment(
    "amazon_climate_pledge_fund", "pachama",
    "Series A", "series-a", "2020-12-16",
    15_000_000, "USD", 1, 0.97,
    "Amazon Climate Pledge Fund led Pachama (BR) Series A ($15M, Dec 2020). Pachama: AI-powered forest carbon platform using satellite imagery to verify nature-based carbon offsets; enables corporate climate commitments through verified forest protection/restoration. Co-investors: Salesforce Ventures, Future Shape, Social Capital. Source: TechCrunch.",
)

add_investment(
    "salesforce_ventures", "pachama",
    "Series A", "series-a", "2020-12-16",
    None, None, 0, 0.93,
    "Salesforce Ventures co-invested in Pachama (BR) Series A ($15M, Dec 2020) led by Amazon Climate Pledge Fund. Source: TechCrunch.",
)

add_investment(
    "future_shape", "pachama",
    "Series A", "series-a", "2020-12-16",
    None, None, 0, 0.90,
    "Future Shape (Tony Fadell) co-invested in Pachama (BR) Series A ($15M, Dec 2020). Source: TechCrunch.",
)

add_investment(
    "social_capital", "pachama",
    "Series A", "series-a", "2020-12-16",
    None, None, 0, 0.88,
    "Social Capital co-invested in Pachama (BR) Series A ($15M, Dec 2020). Source: TechCrunch.",
)

# ============================================================
# 3. Pachama — Series B ($55M, Jun 2022)
# ============================================================
print()
print("=== Pachama Series B ($55M, Jun 2022) ===")
add_investment(
    "gv_google_ventures", "pachama",
    "Series B", "series-b", "2022-06-16",
    55_000_000, "USD", 1, 0.97,
    "GV (Google Ventures) led Pachama (BR) Series B ($55M, Jun 2022). Pachama grew to 20M+ hectares of forests tracked, 100+ corporate clients. Co-investors: SoftBank Latin America Fund, Amazon Climate Pledge Fund. Source: TechCrunch.",
)

add_investment(
    "softbank_latam", "pachama",
    "Series B", "series-b", "2022-06-16",
    None, None, 0, 0.93,
    "SoftBank Latin America Fund co-invested in Pachama (BR) Series B ($55M, Jun 2022) led by GV. Source: TechCrunch.",
)

add_investment(
    "amazon_climate_pledge_fund", "pachama",
    "Series B", "series-b", "2022-06-16",
    None, None, 0, 0.90,
    "Amazon Climate Pledge Fund continued investment in Pachama Series B ($55M, Jun 2022). Source: TechCrunch.",
)

# ============================================================
# 4. Strider — SP Ventures growth/Series A
# ============================================================
print()
print("=== Strider (BR) / SP Ventures ===")
add_investment(
    "sp_ventures", "strider-br",
    "Series A", "series-a", "2021-01-01",
    None, None, 1, 0.85,
    "SP Ventures (BR) invested in Strider (BR, Piracicaba) Series A; Strider: farm management and agri-intelligence platform with soil sampling, satellite imagery and AI-driven field analytics; operations across BR (soy, sugarcane, corn). Co-investor: Monashees. Source: SP Ventures portfolio page.",
)

# ============================================================
# 5. EcoSea (CL) — IDB Lab investment + CORFO support
# ============================================================
print()
print("=== EcoSea (CL) / IDB Lab + CORFO ===")
add_investment(
    "idb_lab", "ecosea",
    "Series A", "series-a", "2021-06-01",
    None, None, 1, 0.85,
    "IDB Lab invested in EcoSea (CL) Series A; EcoSea: precision aquaculture monitoring platform using underwater sensors, AI and satellite for sustainable salmon/fish farming in Chile; reduces feed waste, antibiotic use. Source: IDB Lab portfolio.",
)

add_support(
    "corfo", "ecosea", "grant_recipient", 0.82,
    "CORFO provided innovation grant to EcoSea (CL) for development of precision aquaculture monitoring technology; Chilean government support for sustainable aquaculture tech. Source: CORFO portfolio.",
    ECOSEA_URL,
)

# ============================================================
# 6. Copper3D (CL) — CORFO grant + MIT EF Chile
# ============================================================
print()
print("=== Copper3D (CL) / CORFO + MIT EF Chile ===")
add_support(
    "corfo", "copper3d", "grant_recipient", 0.82,
    "CORFO provided SEED/innovation grant to Copper3D (CL, Santiago); Copper3D: antimicrobial 3D printing material technology (PLACTIVE AN1 filament with copper nanoparticles, 99.9% pathogen reduction); applications in medical devices, PPE. Source: CORFO portfolio.",
    COPPER3D_URL,
)

add_support(
    "startup_chile", "copper3d", "accelerator_cohort", 0.80,
    "Copper3D (CL) participated in Start-Up Chile acceleration program; received equity-free funding and mentorship. Source: Start-Up Chile portfolio / company profiles.",
    COPPER3D_URL,
)

conn.commit()
print()
print("Total entities:", conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0])
print("Total investment_edges:", conn.execute("SELECT COUNT(*) FROM investment_edges").fetchone()[0])
print("Total support_edges:", conn.execute("SELECT COUNT(*) FROM support_edges").fetchone()[0])
conn.close()
