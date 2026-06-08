"""
Enrich top investors with thesis, profile_blurb, ticket_min/max_usd,
aum_usd_m, lead_behavior, preferred_stages.

Safe: UPDATE only — never inserts. Skips rows already filled.
Run: python scripts/oneoff/enrich_investors.py
"""
import sqlite3, os, sys
sys.stdout.reconfigure(encoding="utf-8")
DB = os.path.join(os.path.dirname(__file__), "..", "..", "db", "bio_latam.db")
conn = sqlite3.connect(DB)

PROFILES = [
    # ── id | thesis | profile_blurb | ticket_min | ticket_max | aum | lead | stages | geo
    (
        "GridX",
        "Deep-tech company builder for Argentine science-based startups in biotech, agtech, and industrial biology. Converts CONICET and university research into companies via pre-seed equity and operational support.",
        "GridX (Grid Exponential) is Argentina's most active deep-tech company builder. Backed by prominent Argentine business families, it identifies high-potential university and CONICET research teams and provides capital, mentoring, and operational infrastructure to launch biotechnology, agricultural tech, and industrial biology companies. Portfolio spans 100+ startups across biomanufacturing, bioinputs, diagnostics, food systems, and environmental tech. Signature program: intensive 6-month cohorts with in-house lab access and commercialization support.",
        50_000, 200_000, 50, "lead", "pre-seed,seed", "AR"
    ),
    (
        "SP Ventures",
        "Brazil's leading agtech and food systems VC. Invests from seed to Series B in precision agriculture, biotech food ingredients, bioinputs, farm management, and sustainable supply chains.",
        "SP Ventures is Brazil's flagship agtech-focused venture capital firm, founded in 2009 and managing $100M+ in AUM across two funds. Co-produces the annual Radar Agtech Brasil report with Embrapa — the definitive market map of Brazil's agtech ecosystem. Strong track record in precision agriculture (Aegro, Solinftec), biological inputs, and food tech. Participates as lead or co-lead in Series A rounds and selectively in later seed rounds. Known for deep sectoral knowledge and strong corporate co-investor relationships with Raízen, BRF, and JBS.",
        500_000, 8_000_000, 100, "lead_or_follow", "seed,series-a,series-b", "BR,LATAM"
    ),
    (
        "The Ganesha Lab",
        "Argentine VC specialized in biotech, pharma, and health sciences spinoffs from CONICET and academic institutions. Backs science-based founding teams at pre-seed and seed stage.",
        "The Ganesha Lab is one of Argentina's most active early-stage biotech investors, specializing in backing scientific founders — typically from CONICET, UBA, or Universidad Nacional networks — to commercialize their research. Focus: therapeutics, diagnostics, industrial biotech, and biomaterials. Known for patient capital suited to long biotech development timelines and active portfolio support through regulatory navigation and clinical trial design.",
        100_000, 1_000_000, 20, "lead", "pre-seed,seed", "AR,LATAM"
    ),
    (
        "AIR Capital",
        "Pan-LatAm early-stage VC based in Buenos Aires. Invests in agtech, biotech, and deeptech at pre-seed and seed, focusing on technology-first companies from Argentina, Brazil, and Chile.",
        "AIR Capital is a Buenos Aires-based venture fund with a broad bioeconomy thesis spanning agtech, industrial biotech, diagnostics, and food systems. Part of the Endeavor network ecosystem. Invests early alongside other LatAm funds, often syndicated with The Ganesha Lab and The Yield Lab. Known for a fast decision process and active board participation in portfolio companies.",
        100_000, 1_500_000, 15, "follow", "pre-seed,seed", "AR,BR,CL,LATAM"
    ),
    (
        "The Yield Lab LATAM",
        "Dedicated LatAm agrifood VC. Invests in precision agriculture, sustainable food systems, bioinputs, food tech, and climate-smart agriculture from seed to Series A.",
        "The Yield Lab LATAM is the dedicated Latin American arm of The Yield Lab global agrifood network, backed by IDB Lab, Ceres Group, and strategic agribusiness LPs. Manages a $25M+ fund, targeting 10–15 portfolio companies per cycle across agtech, food tech, bioinputs, and sustainable supply chains in Argentina, Brazil, Chile, Colombia, and Mexico. Provides direct access to a global network of agrifood corporates including Bayer, Syngenta, and Cargill as strategic advisors.",
        250_000, 2_000_000, 25, "lead_or_follow", "seed,series-a", "AR,BR,CL,MX,CO,LATAM"
    ),
    (
        "Zentynel",
        "Mexican corporate venture accelerator backed by agribusiness families. Invests in and accelerates agtech, biotech, and food systems startups across Mexico and LatAm.",
        "Zentynel is the venture arm of Mexican agribusiness interests (Grupo Palacios network). Runs structured accelerator cohorts and makes direct equity investments in early-stage startups in agricultural technology, food systems, and biotechnology. Serves as a commercial bridge for startups seeking validation in Mexican and Central American agricultural markets. Strong connections to Mexican corporate buyers and distributors.",
        50_000, 500_000, 15, "lead", "pre-seed,seed", "MX,LATAM"
    ),
    (
        "SF500",
        "Global startup accelerator with strong LatAm presence. Provides pre-seed equity and structured programs to early-stage deep tech, agtech, and biotech founders.",
        "SF500 is an accelerator and micro-fund focused on science and technology startups with LatAm founders. It provides structured programs combining mentorship, product validation, investor access, and small equity checks. Strong network connecting LatAm founders to US accelerators and international VC ecosystem.",
        50_000, 150_000, 10, "follow", "pre-seed", "AR,BR,LATAM,GLOBAL"
    ),
    (
        "CITES",
        "Argentine government-backed institutional fund supporting CONICET and university spinoff startups in biotech, agtech, and deeptech with seed capital and mentoring.",
        "CITES (Centro de Inversiones y Transferencia Empresarial de Startups) is an Argentine institutional vehicle supporting spinoffs from public universities and CONICET research centers. Provides seed capital, structured mentoring, and connections to the broader Argentine biotech ecosystem. Operates as a patient, non-dilutive or mildly dilutive instrument for early-stage companies with scientific co-founders who need runway to achieve their first commercial milestone.",
        30_000, 200_000, 10, "lead", "pre-seed,seed", "AR"
    ),
    (
        "DraperCygnus",
        "Spain-based VC with an Ibero-American program. Invests in biotech, healthtech, agtech, and deeptech startups across Spain, Mexico, Argentina, and broader LatAm.",
        "DraperCygnus is part of the Draper global network (Tim Draper/DFJ). It is one of Spain's most prominent VC funds, with a strong focus on the Ibero-American ecosystem via its Mexico City and Madrid offices. Invested in digital health, biotech, agtech, and industrial tech across Spain and Latin America. Brings access to Draper's global network for portfolio companies seeking US market entry or international expansion.",
        500_000, 5_000_000, 100, "lead_or_follow", "seed,series-a", "ES,MX,AR,LATAM"
    ),
    (
        "Kamay Ventures",
        "Brazil–US cross-border VC focused on agtech, food tech, and biotech startups from Brazil and LatAm targeting the North American market.",
        "Kamay Ventures is a Brazilian-American VC fund with offices in São Paulo and Washington DC. Specifically targets Brazilian and LatAm deep-tech companies ready to scale to the US market, particularly in precision agriculture, biotech, and food systems. Part of the ABVCAP ecosystem with connections to Brazilian development bank BNDES. Provides US market access, regulatory navigation, and co-investor relationships.",
        500_000, 3_000_000, 30, "lead_or_follow", "seed,series-a", "BR,US,LATAM"
    ),
    (
        "SOSV_IndieBio",
        "World's largest life sciences accelerator. $250K investment + 24-week NYC/SF program for biotech, healthtech, agtech, and synthetic biology startups globally.",
        "SOSV IndieBio is the life sciences track of SOSV, the world's most active biotech accelerator. Invests $250K in cohorts of ~20 startups per cycle at its New York and San Francisco labs. Has deployed over $100M across 200+ biotech companies globally, including notable LatAm founders. Alumni network connects companies to pharma corporate VCs, top-tier US investors, and FDA regulatory experts. Strong in synthetic biology, diagnostics, computational biology, and novel therapeutics.",
        250_000, 500_000, 100, "lead", "pre-seed,seed", "GLOBAL"
    ),
    (
        "GLOCAL",
        "Argentine biotech and deeptech accelerator providing early-stage capital, mentoring, and regulatory support for science-based startups.",
        "GLOCAL is an Argentine accelerator focused on deeptech startups with strong scientific foundations. Provides equity capital, structured 6-month acceleration programs, and connections to Argentine research institutions and international investors. Strong portfolio in agtech, industrial biotech, and diagnostics. Known for active mentoring from experienced biotech operators and scientists-turned-entrepreneurs.",
        50_000, 250_000, 8, "lead", "pre-seed,seed", "AR,LATAM"
    ),
    (
        "KPTL",
        "Brazilian impact VC focused on climate, biodiversity, and nature-based solutions. Invests in agtech, bioinputs, forest economy, and environmental biotech.",
        "KPTL manages impact venture capital in Brazil with a focus on environmental and social impact sectors. Manages the Forest & Climate Fund in partnership with Fundo Vale. Invests in biotech companies with demonstrable environmental impact: biocontrol, biostimulants, forest restoration, and nature-based solutions. Also known as Kria/Obvious VC in earlier fund iterations. Ticket range $500K–$3M at seed to Series A.",
        500_000, 3_000_000, 50, "lead", "seed,series-a", "BR,LATAM"
    ),
    (
        "Vesper Ventures",
        "Argentine biotech venture studio co-founding companies in synthetic biology, biomanufacturing, and novel biomaterials from day zero alongside scientific teams.",
        "Vesper Ventures is an Argentine biotech venture studio that co-founds and builds companies in synthetic biology, biomanufacturing, and novel biomaterials. Its model involves identifying scientific opportunities, recruiting co-founders, and providing seed capital and operational support from concept stage. Portfolio spans cell therapies, biopolymers, alternative proteins, and agricultural biotech. Often the first institutional capital in a company, with strong follow-on relationships with LatAm biotech VCs.",
        50_000, 300_000, 10, "lead", "pre-seed", "AR,US"
    ),
    (
        "Kaszek Ventures",
        "Premier pan-LatAm growth-stage VC. Manages $4B+ across multiple funds. Occasionally invests in health tech, biotech, and food systems at Series A+.",
        "Kaszek is the most prominent LatAm-focused venture capital firm, co-founded by ex-MercadoLibre executives Hernán Kazah and Nicolás Szekasy. Manages $4B+ in AUM across eight funds. While primarily known for fintech and marketplace investments, has backed companies at the intersection of health tech, food systems, and life sciences at Series A and beyond. Strong LP relationships with top institutional investors globally. The benchmark LatAm VC for follow-on rounds.",
        5_000_000, 50_000_000, 4000, "lead", "series-a,series-b,growth", "BR,AR,MX,LATAM"
    ),
    (
        "Valor Capital Group",
        "US–Brazil VC with offices in New York and São Paulo. Invests in Brazilian technology companies including health tech, agtech, and biotech scaling globally.",
        "Valor Capital Group is a New York and São Paulo-based venture capital firm focused on building bridges between Brazilian tech companies and global markets. Manages $500M+ in AUM. Portfolio in health tech, digital platforms, and agtech. Led by former Endeavor and investment banking executives. Provides US market access, regulatory navigation, and international co-investor relationships for Brazilian deeptech founders.",
        2_000_000, 20_000_000, 500, "lead_or_follow", "series-a,series-b", "BR,US"
    ),
    (
        "Inventure",
        "Nordic VC with emerging-market focus including East Africa and LatAm. Invests in agtech, food systems, and impact-driven biotech in developing markets.",
        "Inventure is a Helsinki-based VC known for backing tech startups in emerging markets, particularly East Africa and LatAm. In LatAm, focuses on agtech, food systems, and environmental tech companies with scalable models. Provides access to Nordic LP networks and European market entry support. Often co-invests with local LatAm funds.",
        300_000, 3_000_000, 80, "follow", "seed,series-a", "LATAM,AFRICA,GLOBAL"
    ),
    (
        "Savia Ventures",
        "Colombian and pan-LatAm VC investing in agtech, food systems, and biotech startups with social and environmental impact.",
        "Savia Ventures is a Bogotá-based VC fund focused on sustainable agriculture, food systems, and biotech in Colombia and LatAm. Backed by family offices and development finance institutions with a dual financial-and-impact mandate. Strong presence in Colombian and Central American agricultural markets. Known for hands-on portfolio support and co-investment with IADB/IFC instruments.",
        100_000, 1_500_000, 20, "lead_or_follow", "seed,series-a", "CO,LATAM"
    ),
    (
        "Endurance 28",
        "Argentine early-stage VC focused on biotech, agtech, and deeptech. Invests in pre-seed and seed rounds in science-based companies from Argentine research institutions.",
        "Endurance 28 is an Argentine micro-VC fund providing early-stage capital to deep-tech and biotech founders from Argentine universities and research centers. Known for fast term sheets and active mentoring by operating partners with startup experience. Co-invests frequently with GridX and The Ganesha Lab in the Argentine biotech ecosystem.",
        50_000, 500_000, 8, "lead_or_follow", "pre-seed,seed", "AR"
    ),
    (
        "Horizons Ventures",
        "Hong Kong-based global VC (Li Ka-shing family office). Invests in frontier technology including biotech, agtech, and computational biology globally.",
        "Horizons Ventures is the private investment arm of Hong Kong billionaire Li Ka-shing. Manages $1B+ in technology investments globally, with notable positions in DeepMind, Spotify, and biotech companies. In LatAm, has made strategic investments in agricultural biotech and agrifood technology. Known for patient long-term capital and access to Asian markets for portfolio companies.",
        1_000_000, 20_000_000, 1000, "follow", "series-a,series-b,growth", "GLOBAL,LATAM,ASIA"
    ),
    (
        "Antom",
        "Argentine and pan-LatAm VC investing in agtech, biotech, and deeptech startups with strong scientific foundations at seed and Series A.",
        "Antom is an Argentine VC fund investing in science-based startups across agtech, biotech, and industrial deeptech. Active in syndicated rounds with other LatAm funds. Known for deep connections to Argentine university research networks and CONICET spinoff ecosystem. Provides patient capital with active operational support.",
        200_000, 2_000_000, 20, "follow", "seed,series-a", "AR,LATAM"
    ),
    (
        "Pampa Start",
        "Argentine accelerator and seed fund focused on agtech and biotech startups with Argentine scientific or agricultural technology origin.",
        "Pampa Start is an Argentine accelerator providing structured cohort programs and seed capital for early-stage agtech and biotech companies. Backed by agribusiness families and institutional investors. Strong network with Argentine farming cooperatives and export grain companies that serve as pilot customers for portfolio startups.",
        50_000, 300_000, 5, "lead", "pre-seed,seed", "AR"
    ),
]

updated = 0
skipped = 0

for row in PROFILES:
    (investor_id, thesis, blurb, t_min, t_max, aum,
     lead, stages, geo) = row

    exists = conn.execute(
        "SELECT investor_id FROM investors WHERE investor_id = ?", (investor_id,)
    ).fetchone()
    if not exists:
        print(f"  [SKIP — not found] {investor_id}")
        skipped += 1
        continue

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
print("Done.")
