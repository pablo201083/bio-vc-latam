"""Add Nintx Series A investors + FINEP grant.

Source: https://www.businesswire.com/news/home/20241211877241/en/
        https://neofeed.com.br/startups/com-cheque-do-fundo-pitanga-e-de-guilherme-leal...
        https://agencia.fapesp.br/biotech-startup-aims-to-transform-brazils-natural-products...

Nintx (nintx-br, BR) raised US$10M Series A in December 2024:
  - Led by: Pitanga (BR VC), Ecoa Capital (BR impact VC), MOV Investimentos (BR)
  - Non-dilutive: ~US$2M FINEP economic subsidy grant
  - Drug discovery / Brazilian biodiversity / multifactorial diseases
"""
import sqlite3
import hashlib
import datetime
import sys

sys.stdout.reconfigure(encoding="utf-8")
conn = sqlite3.connect("db/bio_latam.db")
now = datetime.datetime.now(datetime.UTC).isoformat()

SOURCE_URL = "https://www.businesswire.com/news/home/20241211877241/en/Biotech-Nintx-Raises-US%24-10-Million-to-Advance-a-New-Generation-of-Medicines-Based-on-Brazilian-Biodiversity"

# --- 1. Add investor entities ---
new_entities = [
    {
        "entity_id": "pitanga",
        "entity_type": "investor",
        "canonical_name": "Pitanga Fund",
        "slug": "pitanga-fund",
        "short_description": "Brazilian VC fund founded 2011 by scientist Fernando Reinach; invests in early-stage science and technology startups in LATAM, with strong focus on biotech.",
        "country_code": "BR",
        "website": "http://www.pitangainvest.com.br",
        "status": "active",
    },
    {
        "entity_id": "ecoa_capital",
        "entity_type": "investor",
        "canonical_name": "Ecoa Capital",
        "slug": "ecoa-capital",
        "short_description": "Brazilian impact VC founded 2021 in Sao Paulo; invests in innovative companies reducing social inequality and environmental degradation; portfolio includes food/agtech and health.",
        "country_code": "BR",
        "website": "https://www.ecoa.capital",
        "status": "active",
    },
    {
        "entity_id": "mov_investimentos",
        "entity_type": "investor",
        "canonical_name": "MOV Investimentos",
        "slug": "mov-investimentos",
        "short_description": "Brazilian impact investor founded 2012; backs entrepreneurs with solutions to social and environmental challenges in Brazil and LATAM.",
        "country_code": "BR",
        "website": "https://www.movinvestimentos.com.br",
        "status": "active",
    },
]

inserted_entities = 0
for ent in new_entities:
    existing = conn.execute(
        "SELECT entity_id FROM entities WHERE entity_id=?", (ent["entity_id"],)
    ).fetchone()
    if not existing:
        conn.execute(
            """INSERT INTO entities
            (entity_id, entity_type, canonical_name, slug, short_description,
             country_code, website, status, last_verified_at)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                ent["entity_id"], ent["entity_type"], ent["canonical_name"],
                ent["slug"], ent["short_description"], ent["country_code"],
                ent["website"], ent["status"], now,
            ),
        )
        print(f"Inserted entity: {ent['entity_id']}")
        inserted_entities += 1
    else:
        print(f"Already exists: {ent['entity_id']}")

# --- 2. Add investment_edges: pitanga/ecoa/mov -> nintx-br (Series A, Dec 2024) ---
inv_rows = [
    # (investor_id, startup_id, round_name, round_stage, announced_date, amount, currency, is_lead, confidence, notes)
    (
        "pitanga", "nintx-br",
        "Series A", "series-a", "2024-12-09",
        10_000_000, "USD", 1, 0.95,
        "Lead investor in Nintx US$10M Series A (Dec 2024). Total round ~$10M from Pitanga, Ecoa Capital, MOV Investimentos + FINEP ~$2M grant.",
    ),
    (
        "ecoa_capital", "nintx-br",
        "Series A", "series-a", "2024-12-09",
        None, None, 0, 0.95,
        "Co-investor in Nintx US$10M Series A (Dec 2024). Led by Pitanga.",
    ),
    (
        "mov_investimentos", "nintx-br",
        "Series A", "series-a", "2024-12-09",
        None, None, 0, 0.95,
        "Co-investor in Nintx US$10M Series A (Dec 2024). Led by Pitanga.",
    ),
]

inserted_inv = 0
for investor_id, startup_id, round_name, round_stage, date, amount, currency, is_lead, conf, notes in inv_rows:
    iid = "inv_" + hashlib.md5(f"{investor_id}|{startup_id}|{round_stage}".encode()).hexdigest()[:8]
    existing = conn.execute(
        "SELECT investment_id FROM investment_edges WHERE investor_id=? AND startup_id=? AND round_stage=?",
        (investor_id, startup_id, round_stage)
    ).fetchone()
    if not existing:
        conn.execute(
            """INSERT INTO investment_edges
            (investment_id, investor_id, startup_id, round_name, round_stage,
             announced_date, amount, currency, is_lead, confidence_score, notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (iid, investor_id, startup_id, round_name, round_stage,
             date, amount, currency, is_lead, conf, notes),
        )
        print(f"Inserted investment: {investor_id} -> {startup_id} ({round_stage})")
        inserted_inv += 1
    else:
        print(f"Already exists: {investor_id} -> {startup_id} ({round_stage})")

# --- 3. Ecoa Capital -> Symbiomics (Series A confirmed) ---
# Tracxn/CBInsights confirm Ecoa Capital invested in Symbiomics Series A alongside The Yield Lab Latam
symb_iid = "inv_" + hashlib.md5("ecoa_capital|symbiomics|series-a".encode()).hexdigest()[:8]
existing_symb = conn.execute(
    "SELECT investment_id FROM investment_edges WHERE investor_id='ecoa_capital' AND startup_id='symbiomics' AND round_stage='series-a'"
).fetchone()
if not existing_symb:
    conn.execute(
        """INSERT INTO investment_edges
        (investment_id, investor_id, startup_id, round_name, round_stage,
         announced_date, amount, currency, is_lead, confidence_score, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (
            symb_iid, "ecoa_capital", "symbiomics",
            "Series A", "series-a", None, None, None, 0, 0.88,
            "Ecoa Capital co-invested in Symbiomics Series A alongside MOV Investimentos and The Yield Lab LATAM (confirmed from Ecoa Capital portfolio page).",
        ),
    )
    print("Inserted investment: ecoa_capital -> symbiomics (series-a)")
    inserted_inv += 1
else:
    print("Already exists: ecoa_capital -> symbiomics (series-a)")

# --- 4. FINEP -> nintx-br (grant_recipient) ---
fid = "finep_nintx_" + hashlib.md5("finep|nintx-br|grant".encode()).hexdigest()[:8]
existing_finep = conn.execute(
    "SELECT support_id FROM support_edges WHERE source_entity_id='finep' AND target_entity_id='nintx-br' AND support_type='grant_recipient'"
).fetchone()
if not existing_finep:
    conn.execute(
        """INSERT OR IGNORE INTO support_edges
        (support_id, source_entity_id, target_entity_id, support_type,
         notes, source_url, confidence_score, added_by, added_at)
        VALUES (?,?,?,?,?,?,?,'human:curador',?)""",
        (
            fid, "finep", "nintx-br", "grant_recipient",
            "FINEP economic subsidy grant (~US$2M non-reimbursable) awarded as part of Nintx US$10M Series A (Dec 2024). Drug discovery platform for multifactorial diseases using Brazilian biodiversity.",
            SOURCE_URL,
            0.93,
            now,
        ),
    )
    print("Inserted: finep -> nintx-br (grant_recipient)")
else:
    print("Already exists: finep -> nintx-br")

conn.commit()
print()
print(f"Entities inserted: {inserted_entities}")
print(f"Investment edges inserted: {inserted_inv}")
print("Total entities:", conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0])
print("Total investment_edges:", conn.execute("SELECT COUNT(*) FROM investment_edges").fetchone()[0])
print("Total support_edges:", conn.execute("SELECT COUNT(*) FROM support_edges").fetchone()[0])
conn.close()
