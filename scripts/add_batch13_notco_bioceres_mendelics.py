"""Batch 13: NotCo full investment history, Bioceres SA SPAC/IPO,
Mendelics Series A, Moolec Science SPAC, and related edges.

Sources:
- NotCo Series B ($30M, Nov 2019): https://techcrunch.com/2019/11/14/notco-a-chilean-food-tech-startup-raises-30-million/
  L Catterton (lead), Kaszek Ventures, SOSV/IndieBio, DFJ
- NotCo Series C ($85M, Jan 2021): https://techcrunch.com/2021/01/07/notco-raises-85-million-series-c/
  L Catterton (lead), Kaszek Ventures, Future Positive Capital
- NotCo Series D ($235M, Jul 2021): https://techcrunch.com/2021/07/07/tiger-global-leads-notcos-235m-series-d/
  Tiger Global (lead), L Catterton, Kaszek Ventures, Jeff Bezos/Bezos Expeditions, 2150, Zoma Capital
- Bioceres SA SPAC (Jun 2019): https://ir.bioceres.com/news-releases/news-release-details/bioceres-crop-solutions-merges-union-acquisition-corp-ii
  SPAC merger with Union Acquisition Corp II → NASDAQ: BIOX
- Mendelics Series A ($5M, Sep 2019): https://exame.com/negocios/mendelics-levanta-r-20-milhoes/
  Monashees (lead), Kaszek Ventures
- Moolec Science SPAC (Mar 2023): https://www.moolec.com/press/moolec-science-completes-business-combination-with-lightjump
  LightJump Acquisition Corp → NASDAQ: MLEC
"""
import sqlite3
import hashlib
import datetime
import sys

sys.stdout.reconfigure(encoding="utf-8")
conn = sqlite3.connect("db/bio_latam.db")
now = datetime.datetime.now(datetime.UTC).isoformat()

NOTCO_TC_B = "https://techcrunch.com/2019/11/14/notco-a-chilean-food-tech-startup-raises-30-million/"
NOTCO_TC_C = "https://techcrunch.com/2021/01/07/notco-raises-85-million-series-c/"
NOTCO_TC_D = "https://techcrunch.com/2021/07/07/tiger-global-leads-notcos-235m-series-d/"
BIOCERES_URL = "https://ir.bioceres.com/news-releases/news-release-details/bioceres-crop-solutions-merges-union-acquisition-corp-ii"
MENDELICS_URL = "https://exame.com/negocios/mendelics-levanta-r-20-milhoes/"
MOOLEC_URL = "https://www.moolec.com/press/moolec-science-completes-business-combination-with-lightjump"


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


# ============================================================
# 1. New investor entities
# ============================================================
add_entity(
    "l_catterton", "investor", "L Catterton", "l-catterton",
    "US global consumer-focused PE/growth equity firm ($35B AUM); backed NotCo in Series B (2019) and led Series C ($85M, Jan 2021); active in food, beverage, health and wellness sectors globally.",
    "US", "https://www.lcatterton.com", "active",
)

add_entity(
    "future_positive_capital", "investor", "Future Positive Capital", "future-positive-capital",
    "European early-growth VC focused on science-based ventures for climate and health; co-invested in NotCo Series C (Jan 2021).",
    "FR", "https://www.futurepositive.vc", "active",
)

add_entity(
    "bezos_expeditions", "investor", "Bezos Expeditions", "bezos-expeditions",
    "Personal investment vehicle of Jeff Bezos; participated in NotCo Series D ($235M, Jul 2021) led by Tiger Global; focus on deep tech, food and climate startups.",
    "US", "https://www.bezosexpeditions.com", "active",
)

add_entity(
    "union_acquisition_corp", "investor", "Union Acquisition Corp. II", "union-acquisition-corp-ii",
    "SPAC (Special Purpose Acquisition Company) listed on NASDAQ; merged with Bioceres SA (CL/AR) in Jun 2019 to create Bioceres Crop Solutions Corp (NASDAQ: BIOX); focused on agricultural innovation.",
    "US", "https://www.nasdaq.com/market-activity/stocks/biox", "inactive",
)

add_entity(
    "lightjump_acquisition", "investor", "LightJump Acquisition Corp", "lightjump-acquisition-corp",
    "SPAC that merged with Moolec Science (AR/UK) in Mar 2023 to take the company public on NASDAQ (MLEC); focused on food biotech.",
    "US", "https://www.nasdaq.com/market-activity/stocks/mlec", "inactive",
)

# ============================================================
# 2. NotCo — Full investment history (Series B, C, D)
# ============================================================
print()
print("=== NotCo Series B ($30M, Nov 2019) ===")
add_investment(
    "l_catterton", "NotCo",
    "Series B", "series-b", "2019-11-14",
    30_000_000, "USD", 1, 0.95,
    "L Catterton led NotCo Series B ($30M, Nov 2019); NotCo: Chilean AI-driven plant-based food company (The Not Burger, The Not Chicken); co-investors Kaszek Ventures and SOSV/IndieBio. Source: TechCrunch.",
)

add_investment(
    "kaszek", "NotCo",
    "Series B", "series-b", "2019-11-14",
    None, None, 0, 0.93,
    "Kaszek Ventures co-invested in NotCo Series B ($30M, Nov 2019) led by L Catterton. Source: TechCrunch / Kaszek portfolio.",
)

print()
print("=== NotCo Series C ($85M, Jan 2021) ===")
add_investment(
    "l_catterton", "NotCo",
    "Series C", "series-c", "2021-01-07",
    85_000_000, "USD", 1, 0.95,
    "L Catterton led NotCo Series C ($85M, Jan 2021); NotCo expanded into US market (Whole Foods, Walmart); co-investors Kaszek Ventures, Future Positive Capital. Source: TechCrunch.",
)

add_investment(
    "kaszek", "NotCo",
    "Series C", "series-c", "2021-01-07",
    None, None, 0, 0.93,
    "Kaszek Ventures co-invested in NotCo Series C ($85M, Jan 2021) led by L Catterton. Source: TechCrunch.",
)

add_investment(
    "future_positive_capital", "NotCo",
    "Series C", "series-c", "2021-01-07",
    None, None, 0, 0.90,
    "Future Positive Capital co-invested in NotCo Series C ($85M, Jan 2021). Source: TechCrunch.",
)

print()
print("=== NotCo Series D ($235M, Jul 2021) ===")
add_investment(
    "tiger_global", "NotCo",
    "Series D", "series-d", "2021-07-07",
    235_000_000, "USD", 1, 0.97,
    "Tiger Global Management led NotCo Series D ($235M, Jul 2021); valued NotCo at $1.5B (unicorn). Co-investors: L Catterton, Kaszek Ventures, Bezos Expeditions (Jeff Bezos), 2150. NotCo: AI-powered plant-based food platform ('Giuseppe' AI) operating in CL, AR, BR, CO, US. Source: TechCrunch.",
)

add_investment(
    "l_catterton", "NotCo",
    "Series D", "series-d", "2021-07-07",
    None, None, 0, 0.93,
    "L Catterton co-invested in NotCo Series D ($235M, Jul 2021) led by Tiger Global. Continued investment from Series B and C. Source: TechCrunch.",
)

add_investment(
    "kaszek", "NotCo",
    "Series D", "series-d", "2021-07-07",
    None, None, 0, 0.93,
    "Kaszek Ventures co-invested in NotCo Series D ($235M, Jul 2021) led by Tiger Global. Long-term LATAM VC backer of NotCo since Series B. Source: TechCrunch.",
)

add_investment(
    "bezos_expeditions", "NotCo",
    "Series D", "series-d", "2021-07-07",
    None, None, 0, 0.90,
    "Bezos Expeditions (Jeff Bezos personal fund) co-invested in NotCo Series D ($235M, Jul 2021) led by Tiger Global. Source: TechCrunch.",
)

# ============================================================
# 3. Bioceres SA — SPAC/IPO merger (Jun 2019)
# ============================================================
print()
print("=== Bioceres SA — SPAC merger (Jun 2019) ===")
add_investment(
    "union_acquisition_corp", "bioceres_sa",
    "SPAC Merger / IPO", "ipo", "2019-06-25",
    None, None, 1, 0.97,
    "Bioceres SA (AR) merged with Union Acquisition Corp. II SPAC (Jun 25, 2019) to list on NASDAQ as Bioceres Crop Solutions Corp (BIOX). Bioceres: agronomic and industrial biotech (HB4 drought-tolerant wheat, biostimulants, biologicals); founded Rosario AR. SPAC vehicle raised ~$66M. Source: Bioceres IR / NASDAQ.",
)

# ============================================================
# 4. Mendelics — Series A (Sep 2019)
# ============================================================
print()
print("=== Mendelics Series A ($5M, Sep 2019) ===")
add_investment(
    "monashees", "mendelics",
    "Series A", "series-a", "2019-09-01",
    5_000_000, "USD", 1, 0.88,
    "Monashees led Mendelics Series A (~R$20M / ~$5M, Sep 2019); co-investor Kaszek Ventures. Mendelics: Brazilian genetic testing lab (newborn screening, hereditary diseases, pharmacogenomics); São Paulo BR; largest genetic testing lab in LATAM. Source: Exame / Crunchbase.",
)

add_investment(
    "kaszek", "mendelics",
    "Series A", "series-a", "2019-09-01",
    None, None, 0, 0.85,
    "Kaszek Ventures co-invested in Mendelics Series A (~R$20M, Sep 2019) led by Monashees. Source: Exame / Crunchbase.",
)

# ============================================================
# 5. Moolec Science — SPAC (Mar 2023)
# ============================================================
print()
print("=== Moolec Science SPAC / NASDAQ (Mar 2023) ===")
add_investment(
    "lightjump_acquisition", "moolec",
    "SPAC Merger / IPO", "ipo", "2023-03-27",
    35_000_000, "USD", 1, 0.95,
    "Moolec Science merged with LightJump Acquisition Corp (SPAC) to list on NASDAQ (MLEC) on Mar 27, 2023. Raised ~$35M gross. Moolec: CL/UK molecular farming startup engineering oilseeds to express animal proteins (pork, beef) in plants; products: Piggy Sooy (soy + pork myoglobin), Beefy Sooy. Source: Moolec press release / SEC.",
)

conn.commit()
print()
print("Total entities:", conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0])
print("Total investment_edges:", conn.execute("SELECT COUNT(*) FROM investment_edges").fetchone()[0])
conn.close()
