"""
Sprint 2 de aristas: adds ~19 new investor entities + ~50 investment edges.
Sources: web research June 2026. Confidence 0.85 for confirmed rounds, 0.75 estimated.
"""
import sys, os, sqlite3
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from audit import diff_and_log_update

DB = os.path.join(os.path.dirname(__file__), '..', '..', 'db', 'bio_latam.db')
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: Add new entities + investor records
# ─────────────────────────────────────────────────────────────────────────────

NEW_ENTITIES = [
    # (entity_id, entity_type, canonical_name, country_code, short_description)
    ("dynamo",          "fund",  "Dynamo Capital",              "BR", "Gestora brasilera de renta variable de alto convicción; early-investor en re.green"),
    ("gavea_investimentos", "fund", "Gávea Investimentos",      "BR", "Fondo macro y PE fundado por ex-gobernador del Banco Central de Brasil, Arminio Fraga; investor en re.green"),
    ("lanx_capital",    "fund",  "Lanx Capital",                "BR", "Family office de la familia Moreira Salles; lead investor en re.green (BRL389M ronda inicial)"),
    ("caf",             "fund",  "CAF — Banco de Desarrollo de América Latina", "CO", "Banco de desarrollo multilateral LATAM; financia startups de alto impacto con capital semilla"),
    ("left_lane_capital","fund", "Left Lane Capital",           "US", "VC enfocado en consumer y healthcare; lead en Series A de Koltin (USD 7.3M)"),
    ("fors_capital",    "fund",  "FORS Capital",                "BR", "VC brasilero de agtech y bioeconomía; invertió en Contech Brasil (nota convertible)"),
    ("bossa_invest",    "fund",  "Bossa Invest",                "BR", "VC brasilero early-stage; presente en Biosolvit y Sensix"),
    ("ght4_group",      "fund",  "GHT4 Group",                  "BR", "Multi-family office brasilero; lead en Serie A de Biosolvit; portafolio incluye Brain4care y Mendelics"),
    ("venturance",      "fund",  "Venturance Alternative Assets","CL", "VC chileno de ciencias de la vida; co-investor en GeneProDx/ThyroidPrint junto a Fondo Alerce"),
    ("ifc",             "fund",  "IFC — International Finance Corporation", "US", "Rama de inversión privada del Banco Mundial; co-investor en ronda Series C de Kaiima"),
    ("biominas",        "fund",  "Biominas Brasil",             "BR", "Aceleradora e incubadora de biotecnología en Belo Horizonte; early investor en Tismoo y Vyro Bio"),
    ("oxygea",          "fund",  "Oxygea",                      "BE", "CVC de AB InBev enfocado en sostenibilidad y economía circular; investor en growPack"),
    ("alexia_ventures", "fund",  "Alexia Ventures",             "BR", "VC brasilero deep-tech; portfolio incluye NeuralMed"),
    ("horizons_ventures","fund", "Horizons Ventures",           "HK", "Fondo de inversiones privadas de Li Ka-shing; lead investor en ronda Series C de Kaiima (USD 65M)"),
    ("hawthorne_food_ventures","fund","Hawthorne Food Ventures","US", "VC especializado en innovación en alimentos y bioagricultura; lead en ronda seed de ClearLeaf (USD 3.5M)"),
    ("cventures_primus","fund",  "Cventures Primus",            "BR", "VC brasilero early-stage biotech; co-investor en Neoprospecta"),
    ("biomerieux",      "fund",  "bioMérieux",                  "FR", "Líder global en diagnóstico in vitro; adquirió Neoprospecta en ene-2025 (prev. tenía participación accionaria)"),
    ("domo_invest",     "fund",  "DOMO.VC",                     "BR", "VC brasilero agtech y food-tech; investor en Sensix (R$4.9M ronda mayo 2023)"),
    ("bradesco",        "fund",  "Banco Bradesco",              "BR", "Banco privado brasilero; intermediario financiero en ronda de deuda BNDES para re.green"),
]

NEW_INVESTORS = [
    # (investor_id, investor_type, geography_focus, vertical_focus)
    ("dynamo",           "vc",               "BR",       "equities,growth"),
    ("gavea_investimentos","vc",             "BR",       "macro,pe,growth"),
    ("lanx_capital",     "family_office",    "BR",       "impact,growth"),
    ("caf",              "development_finance","LATAM",  "impact,deeptech"),
    ("left_lane_capital","vc",               "US,LATAM", "consumer,healthcare"),
    ("fors_capital",     "vc",               "BR",       "agtech,bioeconomy"),
    ("bossa_invest",     "vc",               "BR",       "deeptech,biotech"),
    ("ght4_group",       "family_office",    "BR",       "healthtech,biotech"),
    ("venturance",       "vc",               "CL",       "lifesciences,medtech"),
    ("ifc",              "development_finance","GLOBAL", "growth,impact"),
    ("biominas",         "accelerator",      "BR",       "biotech,lifesciences"),
    ("oxygea",           "corporate_vc",     "GLOBAL",   "sustainability,circulareconomy"),
    ("alexia_ventures",  "vc",               "BR",       "deeptech,ai"),
    ("horizons_ventures","vc",               "HK,GLOBAL","deeptech,agbio"),
    ("hawthorne_food_ventures","vc",         "US",       "food,agbio"),
    ("cventures_primus", "vc",               "BR",       "biotech,healthtech"),
    ("biomerieux",       "corporate_vc",     "GLOBAL",   "diagnostics,biotech"),
    ("domo_invest",      "vc",               "BR",       "agtech,foodtech"),
    ("bradesco",         "bank",             "BR",       "generalist"),
]

# Also add BNDES and CORFO to investors table (entities already exist)
EXISTING_ENTITY_NEW_INVESTORS = [
    ("bndes",  "development_finance", "BR",    "infrastructure,biotech,industry"),
    ("corfo",  "development_finance", "CL",    "innovation,science,entrepreneurship"),
]

added_entities = 0
added_investors = 0
skipped = 0

for entity_id, entity_type, canonical_name, country_code, short_desc in NEW_ENTITIES:
    exists = conn.execute("SELECT entity_id FROM entities WHERE entity_id=?", (entity_id,)).fetchone()
    if exists:
        print(f"  entity exists, skip: {entity_id}")
        skipped += 1
        continue
    slug = entity_id.replace("_", "-")
    conn.execute(
        "INSERT INTO entities (entity_id, entity_type, canonical_name, slug, country_code, short_description, status) VALUES (?,?,?,?,?,?,?)",
        (entity_id, entity_type, canonical_name, slug, country_code, short_desc, "active")
    )
    added_entities += 1
    print(f"  + entity: {entity_id}")

conn.commit()

for investor_id, investor_type, geo_focus, vertical_focus in NEW_INVESTORS:
    exists = conn.execute("SELECT investor_id FROM investors WHERE investor_id=?", (investor_id,)).fetchone()
    if exists:
        print(f"  investor exists, skip: {investor_id}")
        skipped += 1
        continue
    conn.execute(
        "INSERT INTO investors (investor_id, investor_type, geography_focus, vertical_focus, active_status) VALUES (?,?,?,?,?)",
        (investor_id, investor_type, geo_focus, vertical_focus, 1)
    )
    added_investors += 1
    print(f"  + investor: {investor_id}")

conn.commit()

for investor_id, investor_type, geo_focus, vertical_focus in EXISTING_ENTITY_NEW_INVESTORS:
    exists = conn.execute("SELECT investor_id FROM investors WHERE investor_id=?", (investor_id,)).fetchone()
    if exists:
        print(f"  investor exists, skip: {investor_id}")
        skipped += 1
        continue
    conn.execute(
        "INSERT INTO investors (investor_id, investor_type, geography_focus, vertical_focus, active_status) VALUES (?,?,?,?,?)",
        (investor_id, investor_type, geo_focus, vertical_focus, 1)
    )
    added_investors += 1
    print(f"  + investor (existing entity): {investor_id}")

conn.commit()

print(f"\nEntities added: {added_entities}, Investors added: {added_investors}, Skipped: {skipped}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2: Add investment edges
# ─────────────────────────────────────────────────────────────────────────────
# Format: (investment_id, investor_id, startup_id, round_stage, announced_date,
#          amount, currency, is_lead, confidence_score, notes)

EDGES = [
    # ── SERIES C+ ────────────────────────────────────────────────────────────
    # Kaiima raised $65M Series C from Horizons, IFC, Infinity; earlier DFJ rounds
    # IFC (World Bank) confirms via press
    ("sprint2-horizons-kaiima",     "horizons_ventures",  "kaiima",       "series-c", "2013-09-01",  65000000, "USD", 1, 0.90, "Lead USD 65M Series C w/ IFC and Infinity Group; Source: PRNewswire Sept 2013"),
    ("sprint2-ifc-kaiima",          "ifc",                "kaiima",       "series-c", "2013-09-01",  None,     "USD", 0, 0.88, "Co-investor Series C USD 65M round; IFC/World Bank; Source: Kaiima PR"),

    # ── SERIES A ─────────────────────────────────────────────────────────────
    # Biosolvit: GHT4 Group lead, Bossa Invest co-invest; $5.58M
    ("sprint2-ght4-biosolvit",      "ght4_group",         "biosolvit",    "series-a", None,          5580000, "USD", 1, 0.88, "Lead Series A; GHT4 also invested in Brain4care, Mendelics; Source: Entrepreneur MENA 2023"),
    ("sprint2-bossa-biosolvit",     "bossa_invest",       "biosolvit",    "series-a", None,          None,    "USD", 0, 0.85, "Co-investor Series A; Source: CBInsights/Crunchbase"),

    # Contech Brasil: FORS Capital (Convertible Note)
    ("sprint2-fors-contech",        "fors_capital",       "contech_brasil","seed",    None,          None,    "BRL", 0, 0.80, "Convertible Note round; FORS Capital Brazil agtech VC; Source: Crunchbase"),

    # ThyroidPrint (GeneProDx Chile): Fondo Alerce $1.4M, CORFO $300K, Venturance
    ("sprint2-alerce-thyroid",      "fondo_alerce",       "thyroidprint", "series-a", "2022-01-01",  1400000, "USD", 1, 0.92, "Lead USD 1.4M in ThyroidPrint/GeneProDx for thyroid cancer molecular test; Source: LAVCA / LatamList"),
    ("sprint2-corfo-thyroid",       "corfo",              "thyroidprint", "series-a", "2022-01-01",  300000,  "USD", 0, 0.88, "USD 300K CORFO grant/investment; Source: GenomeWeb / LatamList"),
    ("sprint2-ventur-thyroid",      "venturance",         "thyroidprint", "series-a", "2022-01-01",  None,    "USD", 0, 0.82, "Co-investor Series A; Venturance Alternative Assets Chile; Source: Venturance.cl / Crunchbase"),

    # Eva / Eden (MX): Kaszek, Y Combinator, Dalus Capital; Series A $22M
    ("sprint2-kaszek-evamx",        "kaszek",             "eva-mx",       "series-a", "2021-01-01",  None,    "USD", 1, 0.88, "Lead investor Series A $22M; Kaszek page confirms eden/eva portfolio; Source: Kaszek.com"),
    ("sprint2-yc-evamx",            "y_combinator",       "eva-mx",       "accelerator","2019-01-01",500000,  "USD", 0, 0.85, "YC batch alumni; Source: multiple press reports Kaszek/Khosla/YC"),
    ("sprint2-dalus-evamx",         "dalus_capital",      "eva-mx",       "series-a", "2024-01-01",  None,    "USD", 0, 0.83, "Participated in 2024 $10M round led by Sierra Ventures; Source: contxto.com"),

    # Koltin (MX): Left Lane Capital lead $7.3M Series A; 500 LatAm
    ("sprint2-leftlane-koltin",     "left_lane_capital",  "koltin-mx",    "series-a", "2024-09-01",  7300000, "USD", 1, 0.92, "Lead USD 7.3M Series A; senior health insurance Mexico; Source: PRNewswire Sept 2024"),
    ("sprint2-500-koltin",          "500_latam",          "koltin-mx",    "series-a", "2024-09-01",  None,    "USD", 0, 0.88, "Co-investor Series A USD 7.3M; Source: PRNewswire / LatamList"),

    # ── GROWTH ───────────────────────────────────────────────────────────────
    # re.green: Lanx Capital + Gávea + Dynamo initial BRL 389M; BNDES BRL 80M debt
    ("sprint2-lanx-regreen",        "lanx_capital",       "re_green",     "growth",   "2021-06-01",  None,    "BRL", 1, 0.90, "Moreira Salles FO lead; BRL 389M initial cap w/ Gávea & Dynamo; Source: LAVCA"),
    ("sprint2-gavea-regreen",       "gavea_investimentos","re_green",     "growth",   "2021-06-01",  None,    "BRL", 0, 0.90, "Co-investor BRL 389M initial; Gávea (Arminio Fraga); Source: LAVCA"),
    ("sprint2-dynamo-regreen",      "dynamo",             "re_green",     "growth",   "2021-06-01",  None,    "BRL", 0, 0.90, "Co-investor BRL 389M initial; Dynamo Capital; Source: LAVCA"),
    ("sprint2-bndes-regreen",       "bndes",              "re_green",     "growth",   "2025-05-01",  14130000,"USD", 0, 0.92, "BRL 80M (USD ~14.1M) financing via BNDES/Bradesco; Source: Reuters May 2025"),

    # ── SEED ─────────────────────────────────────────────────────────────────
    # InEdita Bio (BR pre-seed): Vesper + Ecoa
    ("sprint2-vesper-inedita",      "vesper_ventures",    "inedita-bio-br","pre-seed", "2023-01-01", None,    "USD", 1, 0.90, "Co-founder/lead investor; Source: Crunchbase / AgFunderNews Dec 2025"),
    ("sprint2-ecoa-inedita",        "ecoa_capital",       "inedita-bio-br","pre-seed", "2023-01-01", None,    "USD", 0, 0.88, "Co-investor pre-seed; Source: Crunchbase"),

    # Hapiseeds (BR pre-seed): Vesper
    ("sprint2-vesper-hapi",         "vesper_ventures",    "hapiseeds-br", "pre-seed", None,         None,    "USD", 1, 0.85, "Vesper Ventures portfolio company; Source: Vesper website"),

    # Reddot Bio (BR pre-seed): Vesper
    ("sprint2-vesper-reddot",       "vesper_ventures",    "reddot-bio-br","pre-seed", None,         None,    "USD", 1, 0.85, "Vesper Ventures portfolio company; Source: Vesper website"),

    # Cellertz Bio (BR pre-seed): Vesper
    ("sprint2-vesper-cellertz",     "vesper_ventures",    "cellertz-bio-br","pre-seed",None,        None,    "USD", 1, 0.85, "Vesper Ventures portfolio company; Source: Vesper website"),

    # Vyro Bio (BR seed): Vesper + Biominas
    ("sprint2-vesper-vyro",         "vesper_ventures",    "vyro-bio-br",  "seed",     None,         None,    "USD", 1, 0.88, "Vesper Ventures lead; Zika oncolytic virus CNS tumors; Source: Crunchbase / Labiotech"),
    ("sprint2-biominas-vyro",       "biominas",           "vyro-bio-br",  "seed",     None,         None,    "BRL", 0, 0.80, "Biominas Brasil accelerator & co-investor; Source: Tracxn / Crunchbase"),

    # NeuralMed (BR seed): IDB Invest + Alexia Ventures + YAYA
    ("sprint2-idb-neuralmed",       "idb_invest",         "neuralmed",    "seed",     "2021-08-16", 1900000, "USD", 0, 0.85, "USD 1.9M Seed 2021; IDB Invest co-investor; Source: Crunchbase"),
    ("sprint2-alexia-neuralmed",    "alexia_ventures",    "neuralmed",    "seed",     "2021-08-16", None,    "USD", 0, 0.85, "Co-investor seed; Source: Alexia.vc portfolio"),

    # Neoprospecta (BR seed): CAF + Cventures Primus + bioMérieux
    ("sprint2-caf-neopros",         "caf",                "neoprospecta-br","seed",   "2021-01-01", None,    "BRL", 0, 0.90, "CAF R$2.5M investment via FIDE fund; COVID testing startup; Source: CAF.com press release"),
    ("sprint2-cventures-neopros",   "cventures_primus",   "neoprospecta-br","seed",   None,         None,    "USD", 0, 0.78, "Co-investor; Cventures Primus BR early-stage VC; Source: Crunchbase"),
    ("sprint2-biomx-neopros",       "biomerieux",         "neoprospecta-br","seed",   None,         None,    "USD", 0, 0.82, "Strategic investor pre-acquisition; bioMérieux acquired 100% Jan 2025; Source: bioMerieux press"),

    # Tismoo (BR pre-seed): Biominas
    ("sprint2-biominas-tismoo",     "biominas",           "tismoo",       "pre-seed", None,         None,    "BRL", 0, 0.80, "Biominas Brasil institutional investor; sole documented VC; Source: Tracxn"),

    # growPack (AR seed): Oxygea (AB InBev CVC) + Irani Ventures
    ("sprint2-oxygea-growpack",     "oxygea",             "growpack",     "seed",     "2024-03-06", 303000,  "USD", 1, 0.88, "USD 303K Seed Mar 2024 led by Oxygea (AB InBev CVC); bioplastics; Source: Signalbase / Tracxn"),

    # Sensix (BR seed): GLOCAL + Bossa Invest + DOMO.VC
    ("sprint2-glocal-sensix",       "glocal",             "sensix",       "seed",     "2023-05-01", None,    "BRL", 0, 0.82, "Co-investor; GLOCAL Argentina VC active in BR; Source: CBInsights"),
    ("sprint2-bossa-sensix",        "bossa_invest",       "sensix",       "seed",     "2023-05-01", None,    "BRL", 0, 0.82, "Co-investor R$4.9M round May 2023 w/ SLC Agricola; Source: Bloomberg Línea"),
    ("sprint2-domo-sensix",         "domo_invest",        "sensix",       "seed",     "2023-05-01", None,    "BRL", 0, 0.82, "Co-investor R$4.9M round; DOMO.VC agtech; Source: Bloomberg Línea"),

    # ClearLeaf (CR seed): Hawthorne Food Ventures lead $3.5M
    ("sprint2-hfv-clearleaf",       "hawthorne_food_ventures","clearleaf", "seed",    "2025-05-01", 3500000, "USD", 1, 0.90, "Lead USD 3.5M Seed May 2025; non-toxic pathogen control; Source: AgriTechTomorrow"),

    # RECEPTA Biopharma (BR pre-seed): BNDES $14.8M (16% equity)
    ("sprint2-bndes-recepta",       "bndes",              "recepta_biopharma","pre-seed","2012-01-01",14800000,"USD",0, 0.90, "BNDES 16% equity stake USD 14.8M (R$28.9M); first BNDES early-stage biotech investment; Source: Ludwig Cancer Research press"),

    # TissueLabs (BR pre-seed): Biominas Brasil + Mergus Ventures
    ("sprint2-biominas-tissue",     "biominas",           "tissuelabs",   "pre-seed", None,         None,    "BRL", 0, 0.78, "Biominas Brasil early investor; Source: Tracxn/Crunchbase"),
]

# ─────────────────────────────────────────────────────────────────────────────
# Insert edges
# ─────────────────────────────────────────────────────────────────────────────
added_edges = 0
skipped_edges = 0
errors = []

for edge in EDGES:
    (inv_id, investor_id, startup_id, round_stage, announced_date,
     amount, currency, is_lead, confidence, notes) = edge

    # Check if investor exists
    inv_ok = conn.execute("SELECT investor_id FROM investors WHERE investor_id=?", (investor_id,)).fetchone()
    if not inv_ok:
        errors.append(f"MISSING INVESTOR: {investor_id} (edge {inv_id})")
        continue

    # Check if startup exists
    st_ok = conn.execute("SELECT entity_id FROM entities WHERE entity_id=?", (startup_id,)).fetchone()
    if not st_ok:
        errors.append(f"MISSING STARTUP: {startup_id} (edge {inv_id})")
        continue

    # Check if edge already exists
    dup = conn.execute("SELECT investment_id FROM investment_edges WHERE investment_id=?", (inv_id,)).fetchone()
    if dup:
        print(f"  edge exists, skip: {inv_id}")
        skipped_edges += 1
        continue

    conn.execute("""
        INSERT INTO investment_edges
        (investment_id, investor_id, startup_id, round_stage, announced_date,
         amount, currency, is_lead, confidence_score, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (inv_id, investor_id, startup_id, round_stage, announced_date,
          amount, currency, is_lead, confidence, notes))
    added_edges += 1
    print(f"  + edge: {investor_id} → {startup_id} ({round_stage})")

conn.commit()

print(f"\n{'='*60}")
print(f"Entities added: {added_entities}")
print(f"Investors added: {added_investors}")
print(f"Edges added: {added_edges}")
print(f"Skipped: {skipped_edges + skipped}")
if errors:
    print(f"\nERRORS ({len(errors)}):")
    for e in errors:
        print(f"  {e}")

# Final counts
total = conn.execute("SELECT COUNT(*) FROM investment_edges").fetchone()[0]
with_edges = conn.execute("SELECT COUNT(DISTINCT startup_id) FROM investment_edges").fetchone()[0]
print(f"\nDB totals → edges: {total}, startups with edges: {with_edges}")

conn.close()
print("Done.")
