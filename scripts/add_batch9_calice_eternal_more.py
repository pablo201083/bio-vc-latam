"""Batch 9: Calice Biotech seed round, Eternal Mycofood investors, more AR startups.

Sources:
- Calice $2.5M seed: https://latamlist.com/calice-raises-2-5m-seed-round/
  Draper Cygnus (lead), Astanor, Xperiment Ventures, AIR Capital, Innventure, GrainCorp Ventures
- Eternal/Kernel Mycofoods: https://www.cbinsights.com/company/kernel-mycofoods
  Plug and Play Japan investor; $15M total raised
- Stamm Biotech $17M Series A (Feb 2022): https://techcrunch.com/2022/02/28/stamm-biotech-raises-17m-for-its-next-generation-3d-printed-bioreactor/
  Varana Capital (lead), Draper Associates, SOSV, Draper Cygnus, Grid Exponential
"""
import sqlite3
import hashlib
import datetime
import sys

sys.stdout.reconfigure(encoding="utf-8")
conn = sqlite3.connect("db/bio_latam.db")
now = datetime.datetime.now(datetime.UTC).isoformat()

CALICE_URL = "https://latamlist.com/calice-raises-2-5m-seed-round/"
ETERNAL_URL = "https://www.cbinsights.com/company/kernel-mycofoods"
STAMM_URL = "https://techcrunch.com/2022/02/28/stamm-biotech-raises-17m-for-its-next-generation-3d-printed-bioreactor/"


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
# 1. New investor/eso entities
# ============================================================
add_entity("draper_cygnus", "investor", "Draper Cygnus", "draper-cygnus",
           "Buenos Aires-based deep tech VC (Seed–Series A) affiliated with Draper Venture Network; invests in LATAM biotech, agtech, fintech, cleantech and space; portfolio includes Calice, Stamm, Splight.",
           "AR", "https://www.drapercygnus.vc", "active")

add_entity("astanor", "investor", "Astanor Ventures", "astanor-ventures",
           "Brussels-based impact VC fund focused on agrifoodtech transformation; invests across Europe and LATAM in sustainable food systems and agricultural innovation; co-invested in Calice AR.",
           "BE", "https://astanor.com", "active")

add_entity("innventure", "investor", "Innventure AgriFood Tech", "innventure-agrifood",
           "Argentine agrifoodtech VC investing in early-stage startups in food, agriculture and biotech across LATAM; portfolio includes Calice.",
           "AR", "https://innventure.vc", "active")

add_entity("xperiment_ventures", "investor", "Xperiment Ventures", "xperiment-ventures",
           "Early-stage VC fund focused on deep tech and frontier tech startups in Latin America; co-invested in Calice AR seed round.",
           "AR", "https://xperiment.vc", "active")

add_entity("plug_and_play", "eso", "Plug and Play Tech Center", "plug-and-play",
           "Global accelerator/corporate innovation platform based in Silicon Valley; runs vertical accelerators (food & beverage, health, agtech, etc.) globally; investor in Eternal Mycofood AR.",
           "US", "https://www.plugandplaytechcenter.com", "active")

add_entity("varana_capital", "investor", "Varana Capital", "varana-capital",
           "US impact VC focused on life sciences and biotech innovations; led Stamm Biotech $17M Series A (Feb 2022).",
           "US", "https://varanacapital.com", "active")

# ============================================================
# 2. Calice Biotech — $2.5M Seed Round
# ============================================================
print()
print("=== Calice Biotech $2.5M Seed ===")
add_investment("draper_cygnus", "calice_biotech",
               "Seed", "seed", "2025-05-23",
               2_500_000, "USD", 1, 0.93,
               "Draper Cygnus led Calice $2.5M seed round (May 2025); co-investors: Astanor, Xperiment Ventures, AIR Capital, Innventure AgriFood Tech, GrainCorp Ventures/Artesian. Calice: AI platform for virtual crop field trials (Nodes product); originally gene editing, pivoted 2023. Source: LatamList / NextBillion / Draper Cygnus portfolio.")

add_investment("astanor", "calice_biotech",
               "Seed", "seed", "2025-05-23",
               None, None, 0, 0.92,
               "Astanor Ventures co-invested in Calice $2.5M seed round (May 2025) led by Draper Cygnus. Astanor: Belgium agrifoodtech impact VC. Source: LatamList.")

add_investment("AIR Capital", "calice_biotech",
               "Seed", "seed", "2025-05-23",
               None, None, 0, 0.92,
               "AIR Capital co-invested in Calice $2.5M seed round (May 2025) led by Draper Cygnus. Source: LatamList.")

add_investment("innventure", "calice_biotech",
               "Seed", "seed", "2025-05-23",
               None, None, 0, 0.92,
               "Innventure AgriFood Tech co-invested in Calice $2.5M seed round (May 2025) led by Draper Cygnus. Source: LatamList.")

add_investment("glocal", "calice_biotech",
               "Seed", "seed", "2025-05-23",
               None, None, 0, 0.90,
               "GLOCAL co-invested in Calice seed round (2025). Source: Calice Crunchbase / investor mentions.")

# ============================================================
# 3. Eternal Mycofood — Plug and Play investor
# ============================================================
print()
print("=== Eternal Mycofood / Plug and Play ===")
add_investment("plug_and_play", "eternal_mycofood",
               "Undisclosed", "undisclosed", None,
               None, None, 0, 0.82,
               "Plug and Play (Japan vertical) invested in Eternal (fka Kernel Mycofoods), Buenos Aires AR; $15M total raised. Eternal: AI-optimized mycoprotein precision fermentation ingredients. Source: CBInsights / Eternal website.")

# ============================================================
# 4. Stamm Biotech — Varana Capital Series A
# ============================================================
# Note: existing DB has DraperCygnus/SOSV/GridX/AIR Capital edges labeled 'series-b' incorrectly
# The confirmed Series A ($17M, Feb 2022) lead is Varana Capital
# Adding Varana as lead; NOT correcting existing edges (requires audit)
print()
print("=== Stamm Biotech / Varana Capital Series A ===")
add_investment("varana_capital", "stamm",
               "Series A", "series-a", "2022-02-28",
               17_000_000, "USD", 1, 0.97,
               "Varana Capital led Stamm Biotech $17M Series A (Feb 28, 2022); existing investors Draper Associates, SOSV, Draper Cygnus, Grid Exponential also participated; new investors: Vista, New Abundance, Trillian. Stamm: desktop 3D-printed microfluidic bioreactors for cell biology/bioproduction. Total raised: $20M. Source: TechCrunch / Varana Capital press release.")

conn.commit()
print()
print("Total entities:", conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0])
print("Total investment_edges:", conn.execute("SELECT COUNT(*) FROM investment_edges").fetchone()[0])
conn.close()
