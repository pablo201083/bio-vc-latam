"""
Segundo pase: inversores sin profile_blurb, usando los investor_ids reales.
"""
import sqlite3, os, sys
sys.stdout.reconfigure(encoding="utf-8")
DB = os.path.join(os.path.dirname(__file__), "..", "..", "db", "bio_latam.db")
conn = sqlite3.connect(DB)

PROFILES = [
    # id | thesis | profile_blurb | t_min | t_max | aum | lead | stages | geo
    (
        "glocal",
        "Argentine biotech and deeptech accelerator providing early-stage capital, mentoring, and regulatory support for science-based startups.",
        "GLOCAL is an Argentine accelerator focused on deeptech startups with strong scientific foundations. Provides equity capital, 6-month acceleration programs, and connections to Argentine research institutions and international investors. Strong portfolio in agtech, industrial biotech, and diagnostics. Known for active mentoring from experienced biotech operators.",
        50_000, 250_000, 8, "lead", "pre-seed,seed", "AR,LATAM"
    ),
    (
        "inventure",
        "Nordic VC with emerging-market focus including East Africa and LatAm. Invests in agtech, food systems, and impact-driven biotech in developing markets.",
        "Inventure is a Helsinki-based VC known for backing tech startups in emerging markets, particularly East Africa and LatAm. In LatAm focuses on agtech, food systems, and environmental tech companies. Provides access to Nordic LP networks and European market entry support.",
        300_000, 3_000_000, 80, "follow", "seed,series-a", "LATAM,AFRICA,GLOBAL"
    ),
    (
        "DragonesVP",
        "Chilean and pan-LatAm VC focused on agtech, food systems, biotech, and deeptech startups at seed and early Series A.",
        "DragonesVP is a Santiago-based venture capital fund investing in science-based startups across Chile and LatAm. Focuses on food systems, agtech, biotechnology, and industrial technology. Connected to Chilean government programs (CORFO) and the Start-Up Chile alumni network. Known for bridge capital between Chilean and regional VC rounds.",
        200_000, 2_000_000, 20, "lead_or_follow", "seed,series-a", "CL,LATAM"
    ),
    (
        "kptl",
        "Brazilian impact VC focused on climate, biodiversity, and nature-based solutions. Invests in agtech, bioinputs, forest economy, and environmental biotech.",
        "KPTL manages impact venture capital in Brazil with a focus on environmental and social impact sectors. Manages the Forest & Climate Fund in partnership with Fundo Vale, and is known as the merger of Kria and Obvious VC funds. Invests in biotech companies with demonstrable environmental impact: biocontrol, biostimulants, forest restoration, and nature-based solutions. Ticket range BRL 3M–16M (seed to Series A).",
        500_000, 3_000_000, 50, "lead", "seed,series-a", "BR,LATAM"
    ),
    (
        "aceleradora_litoral",
        "Argentine university-linked accelerator providing pre-seed capital and incubation to science-based startups from UNL and Litoral region research centers.",
        "Aceleradora Litoral is a Santa Fe-based startup accelerator affiliated with Universidad Nacional del Litoral (UNL). Provides pre-seed capital, structured mentoring, and access to UNL's research infrastructure and patent portfolio. Focus on agtech, food biotech, industrial biotech, and environmental technology. Key gateway for CONICET and UNL spinoffs in the Argentine Litoral agricultural region.",
        20_000, 100_000, 5, "lead", "pre-seed", "AR"
    ),
    (
        "endurance_28",
        "Argentine early-stage VC focused on biotech, agtech, and deeptech. Invests in pre-seed and seed science-based companies from Argentine research institutions.",
        "Endurance 28 is an Argentine micro-VC fund providing early-stage capital to deep-tech and biotech founders from Argentine universities and research centers. Known for fast term sheets and active mentoring by operating partners with startup experience. Co-invests frequently with GridX and The Ganesha Lab in the Argentine biotech ecosystem.",
        50_000, 500_000, 8, "lead_or_follow", "pre-seed,seed", "AR"
    ),
    (
        "pampa_start",
        "Argentine accelerator and seed fund focused on agtech and biotech startups with agricultural or scientific origin.",
        "Pampa Start is an Argentine accelerator providing structured cohort programs and seed capital for early-stage agtech and biotech companies. Backed by agribusiness families and institutional investors. Strong network with Argentine farming cooperatives and export companies that serve as pilot customers for portfolio startups.",
        50_000, 300_000, 5, "lead", "pre-seed,seed", "AR"
    ),
    (
        "barn_investimentos",
        "Brazilian agtech and food systems seed fund investing in early-stage technology companies transforming Brazilian agribusiness.",
        "Barn Investimentos is a Brazilian seed fund focused on agtech and food systems startups. Provides seed capital and acceleration-style support to early-stage founders building technology for Brazilian agribusiness, food processing, and sustainability. Connected to major Brazilian agro-industrial players as strategic co-investors.",
        100_000, 1_000_000, 10, "lead_or_follow", "pre-seed,seed", "BR"
    ),
    (
        "bossa_invest",
        "Brazilian early-stage VC (BossaNova Investimentos). Invests in seed and pre-seed startups across technology sectors including biotech, healthtech, and agtech.",
        "BossaNova Investimentos (Bossa Invest) is one of Brazil's most active early-stage VCs, with 200+ portfolio companies across technology sectors. Known for high-volume seed investing with a portfolio-driven approach. In biotech and agtech, invests in startups with digital components: precision agriculture, digital health, and biotech-enabled platforms. Provides founder networks, investor access, and Brazilian corporate co-investment.",
        100_000, 500_000, 50, "follow", "pre-seed,seed", "BR"
    ),
    (
        "biominas",
        "Brazilian biotech ecosystem organization and fund (Biominas Brasil). Manages the largest Brazilian biotech hub in Belo Horizonte and provides seed investment to life sciences startups.",
        "Biominas Brasil operates the largest biotech hub in Latin America, located in Belo Horizonte, Minas Gerais. Manages a biotech incubator, accelerator, and early-stage fund. Portfolio spans pharma, diagnostics, medical devices, agrochemical biotech, and industrial biotech. Provides lab infrastructure, regulatory support, and seed capital to early-stage life sciences startups. Connected to UFMG, USP, and UNIFESP research programs.",
        50_000, 300_000, 15, "lead", "pre-seed,seed", "BR"
    ),
    (
        "chileglobal_ventures",
        "Chilean corporate VC and startup scouting network. Connects Chilean and LatAm startups with international corporate partners and investors.",
        "ChileGlobal Ventures is a Santiago-based venture capital initiative focused on connecting Chilean and LatAm technology startups with international corporate co-investors and strategic partners. Backed by Chilean business groups and CORFO. Active in agtech, food tech, cleantech, and biotech. Provides market access to Chilean agrifood companies and government-backed pilot programs.",
        200_000, 2_000_000, 20, "follow", "seed,series-a", "CL,LATAM"
    ),
    (
        "dalus_capital",
        "Mexican VC focused on health tech, biotech, and agtech startups in Mexico and LatAm. Invests at seed and Series A with digital health as a primary thesis.",
        "Dalus Capital is a Mexico City-based venture capital fund focused on health technology, biotech, and agtech in Mexico and LatAm. Manages two funds totaling $60M+. Strong portfolio in digital health (telemedicine, diagnostics, preventive care) and agricultural technology. Known for strong co-investment relationships with IMSS, Mexican hospital networks, and agricultural distributors as pilot customers.",
        500_000, 3_000_000, 60, "lead_or_follow", "seed,series-a", "MX,LATAM"
    ),
    (
        "newtopia_vc",
        "VC fund focused on Mexican and LatAm early-stage tech startups including health tech, biotech, and food systems at seed stage.",
        "Newtopia VC is a Mexico City and Miami-based venture fund investing at the intersection of technology and human potential — health, education, and productivity. In biotech and health tech, focuses on diagnostics, personalized medicine, and preventive health startups with Mexican and LatAm market traction. Backed by experienced operators and entrepreneurs from the Mexican tech ecosystem.",
        250_000, 2_000_000, 30, "follow", "pre-seed,seed", "MX,LATAM"
    ),
    (
        "vox_capital",
        "Brazilian impact VC focused on health access, education, and financial inclusion for low-income populations. Invests in health tech and diagnostics startups.",
        "Vox Capital is a São Paulo-based impact venture capital firm managing $100M+ in AUM across three funds. Primary focus: technology solutions improving quality of life for Brazil's low-income population. In health tech and biotech, invests in diagnostics, telemedicine, and preventive health companies with accessible pricing models. Known for rigorous impact measurement and ESG reporting standards.",
        500_000, 3_000_000, 100, "follow", "seed,series-a", "BR"
    ),
]

updated = 0
skipped = 0

for row in PROFILES:
    (investor_id, thesis, blurb, t_min, t_max, aum,
     lead, stages, geo) = row

    exists = conn.execute(
        "SELECT investor_id, profile_blurb FROM investors WHERE investor_id = ?", (investor_id,)
    ).fetchone()
    if not exists:
        print(f"  [NOT FOUND] {investor_id}")
        skipped += 1
        continue

    # Only fill empty fields
    conn.execute("""
        UPDATE investors SET
            thesis            = COALESCE(NULLIF(thesis,''), ?),
            profile_blurb     = COALESCE(NULLIF(profile_blurb,''), ?),
            ticket_min_usd    = COALESCE(ticket_min_usd, ?),
            ticket_max_usd    = COALESCE(ticket_max_usd, ?),
            aum_usd_m         = COALESCE(aum_usd_m, ?),
            lead_behavior     = COALESCE(NULLIF(lead_behavior,''), ?),
            preferred_stages  = COALESCE(NULLIF(preferred_stages,''), ?),
            geography_focus   = COALESCE(NULLIF(geography_focus,''), ?)
        WHERE investor_id = ?
    """, (thesis, blurb, t_min, t_max, aum, lead, stages, geo, investor_id))
    updated += 1
    print(f"  ✓ {investor_id}")

conn.commit()
conn.close()
print(f"\nUpdated: {updated}  Skipped: {skipped}")
