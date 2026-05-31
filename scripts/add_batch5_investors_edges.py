"""Batch 5: New investor entities + edges for Traive, Arado, etc.

Sources:
- Traive Series B ($20M, Feb 2024): https://news.fintech.io/post/102izan/traive-raises-20m-in-series-b-funding
  Investors: Banco do Brasil (lead), BASF Venture Capital, FMC Ventures, SP Ventures, Astella Investimentos
- Arado Series A ($12M): https://agfundernews.com/breaking-brazils-arado-nee-clicampo-secures-12m-to-streamline-the-countrys-agribusiness-supply-chain
  Investors: Acre Venture Partners (lead), Syngenta Group Ventures, Globo Ventures, Maya Capital, Valor Capital, SP Ventures
"""
import sqlite3
import hashlib
import datetime
import sys

sys.stdout.reconfigure(encoding="utf-8")
conn = sqlite3.connect("db/bio_latam.db")
now = datetime.datetime.now(datetime.UTC).isoformat()

TRAIVE_URL = "https://news.fintech.io/post/102izan/traive-raises-20m-in-series-b-funding"
ARADO_URL = "https://agfundernews.com/breaking-brazils-arado-nee-clicampo-secures-12m-to-streamline-the-countrys-agribusiness-supply-chain"


def add_entity(entity_id, entity_type, name, slug, desc, country, website, status):
    existing = conn.execute("SELECT entity_id FROM entities WHERE entity_id=?", (entity_id,)).fetchone()
    if not existing:
        conn.execute("""INSERT INTO entities
            (entity_id, entity_type, canonical_name, slug, short_description,
             country_code, website, status, last_verified_at)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (entity_id, entity_type, name, slug, desc, country, website, status, now))
        print(f"Added entity: {entity_id}")
        return True
    else:
        print(f"Already exists entity: {entity_id}")
        return False


def add_investment(investor_id, startup_id, round_name, round_stage, date,
                   amount, currency, is_lead, conf, notes):
    iid = "inv_" + hashlib.md5(f"{investor_id}|{startup_id}|{round_stage}".encode()).hexdigest()[:8]
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
        print(f"Added investment: {investor_id} -> {startup_id} ({round_stage})")
        return True
    else:
        print(f"Already exists: {investor_id} -> {startup_id} ({round_stage})")
        return False


# ============================================================
# New investor entities
# ============================================================
add_entity(
    "basf_venture_capital", "investor",
    "BASF Venture Capital", "basf-venture-capital",
    "Corporate venture arm of BASF SE; invests globally in agtech, biotech, materials and sustainability startups complementary to BASF's business strategy.",
    "DE", "https://www.basf-vc.de", "active",
)

add_entity(
    "fmc_ventures", "investor",
    "FMC Ventures", "fmc-ventures",
    "Corporate venture arm of FMC Corporation (specialty chemicals/crop protection); invests in agtech, biologicals and precision agriculture companies globally.",
    "US", "https://www.fmc.com", "active",
)

add_entity(
    "astella_investimentos", "investor",
    "Astella Investimentos", "astella-investimentos",
    "Brazilian VC firm founded 2010 in São Paulo; invests in seed and Series A Brazilian technology companies across sectors including agtech and fintech.",
    "BR", "https://www.astella.com.br", "active",
)

add_entity(
    "acre_venture_partners", "investor",
    "Acre Venture Partners", "acre-venture-partners",
    "Brazilian VC fund focused on agtech, food and sustainability; backed multiple Brazilian agtech startups including Arado Series A.",
    "BR", "https://www.acre.vc", "active",
)

add_entity(
    "globo_ventures", "investor",
    "Globo Ventures", "globo-ventures",
    "Corporate venture arm of Grupo Globo (Brazil's largest media company); invests in Brazilian technology startups including agtech.",
    "BR", "https://globoventures.com.br", "active",
)

add_entity(
    "maya_capital", "investor",
    "Maya Capital", "maya-capital",
    "Brazilian-Latin American VC firm investing in B2B software and marketplace companies; portfolio includes Brazilian agtech and fintech.",
    "BR", "https://www.mayacapital.com.br", "active",
)

print()
print("=== Adding Traive Series B edges ($20M, Feb 2024) ===")
# Traive Series B (Feb 2024, $20M, led by Banco do Brasil)
add_investment("bb_agro_ventures", "traive", "Series B", "series-b",
               "2024-02-01", 20_000_000, "USD", 1, 0.92,
               "Banco do Brasil led Traive $20M Series B (Feb 2024); total Traive raised $47.8M. AI ag credit risk scoring for Brazilian agriculture. Source: fintech.io / LatamList.")
add_investment("basf_venture_capital", "traive", "Series B", "series-b",
               "2024-02-01", None, None, 0, 0.90,
               "BASF Venture Capital co-invested in Traive $20M Series B (Feb 2024). Traive: AI-powered credit risk platform for Brazilian agribusiness.")
add_investment("fmc_ventures", "traive", "Series B", "series-b",
               "2024-02-01", None, None, 0, 0.90,
               "FMC Ventures co-invested in Traive $20M Series B (Feb 2024).")
add_investment("astella_investimentos", "traive", "Series B", "series-b",
               "2024-02-01", None, None, 0, 0.90,
               "Astella Investimentos co-invested in Traive $20M Series B (Feb 2024).")

print()
print("=== Adding Arado Series A edges ($12M) ===")
# Arado Series A ($12M, led by Acre Venture Partners)
add_investment("acre_venture_partners", "arado", "Series A", "series-a",
               "2023-04-01", 12_000_000, "USD", 1, 0.90,
               "Acre Venture Partners LED Arado (fka Clicampo) $12M Series A; other participants: Syngenta Group Ventures, Globo Ventures, Maya Capital, Valor Capital, SP Ventures. Connects smallholder farmers with restaurants/retailers. Source: AgFunderNews.")
add_investment("globo_ventures", "arado", "Series A", "series-a",
               "2023-04-01", None, None, 0, 0.90,
               "Globo Ventures co-invested in Arado (fka Clicampo) $12M Series A.")
add_investment("maya_capital", "arado", "Series A", "series-a",
               "2023-04-01", None, None, 0, 0.90,
               "Maya Capital co-invested in Arado (fka Clicampo) $12M Series A.")

conn.commit()
print()
print("Total entities:", conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0])
print("Total investment_edges:", conn.execute("SELECT COUNT(*) FROM investment_edges").fetchone()[0])
conn.close()
