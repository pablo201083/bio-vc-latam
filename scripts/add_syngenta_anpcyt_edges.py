"""
Add:
  1. ANPCYT -> chemtest (grant_recipient, EMPRETECNO 2013 confirmed)
  2. syngenta_ventures entity (new CVC entity)
  3. syngenta_ventures -> arado (Series A 2023)
  4. syngenta_ventures -> agrolend (Series C 2024)
"""
import sqlite3
import hashlib
import datetime
import sys

sys.stdout.reconfigure(encoding="utf-8")
conn = sqlite3.connect("db/bio_latam.db")
now = datetime.datetime.now(datetime.UTC).isoformat()


def make_sid(a, b):
    return "sup_" + hashlib.md5((a + "|" + b).encode()).hexdigest()[:8]


def make_iid(investor, startup, suffix=""):
    key = f"manual-{investor}-{startup}{'-' + suffix if suffix else ''}"
    return key[:80]


# ─── 1. ANPCYT → chemtest (grant_recipient) ───────────────────────────────────
existing = conn.execute(
    "SELECT support_id FROM support_edges WHERE source_entity_id='anpcyt' AND target_entity_id='chemtest'"
).fetchone()
if not existing:
    conn.execute("""
        INSERT INTO support_edges
        (support_id, source_entity_id, target_entity_id, support_type,
         notes, source_url, confidence_score, added_by, added_at)
        VALUES (?,?,?,?,?,?,?,"human:curador",?)
    """, (
        make_sid("anpcyt", "chemtest"),
        "anpcyt", "chemtest",
        "grant_recipient",
        "ANPCYT EMPRETECNO 2013 founding grant + EBT 2.0 (equipment, supplies, regulatory consulting). CONICET-UNSAM EBT company (IIBIO). Confirmed by multiple press + World Bank feature + argentina.gob.ar.",
        "https://www.argentina.gob.ar/noticias/chemtest-diagnosticos-de-enfermedades",
        0.92,
        now,
    ))
    print("Inserted: anpcyt -> chemtest (grant_recipient)")
else:
    print("Already exists: anpcyt -> chemtest")

# ─── 2. Add syngenta_ventures entity ──────────────────────────────────────────
existing_ent = conn.execute(
    "SELECT entity_id FROM entities WHERE entity_id='syngenta_ventures'"
).fetchone()
if not existing_ent:
    conn.execute("""
        INSERT INTO entities (entity_id, entity_type, canonical_name, slug, short_description,
                              country_code, website, status, last_verified_at)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (
        "syngenta_ventures",
        "investor",
        "Syngenta Group Ventures",
        "syngenta-group-ventures",
        "Corporate venture capital arm of Syngenta; invests globally in agtech, seeds, biologicals, digital agriculture",
        "CH",
        "https://www.syngentagroupventures.com",
        "active",
        now,
    ))
    print("Inserted entity: syngenta_ventures")
else:
    print("Already exists: syngenta_ventures entity")

# ─── 3. syngenta_ventures -> arado (Series A, April 2023, $12M) ───────────────
iid_arado = make_iid("syngenta_ventures", "arado", "2023-series-a")
existing_ie = conn.execute(
    "SELECT investment_id FROM investment_edges WHERE investor_id='syngenta_ventures' AND startup_id='arado'"
).fetchone()
if not existing_ie:
    conn.execute("""
        INSERT INTO investment_edges
        (investment_id, investor_id, startup_id, round_name, round_stage,
         announced_date, amount, currency, confidence_score, source_id, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (
        iid_arado,
        "syngenta_ventures", "arado",
        "Series A", "series-a",
        "2023-04",
        12_000_000, "USD",
        0.92,
        None,
        "Syngenta Group Ventures participated in $12M Series A led by Acre Venture Partners. Also in round: Globo Ventures, Maya Capital, Valor Capital, SP Ventures. Source: Syngenta Group Ventures news + multiple press.",
    ))
    print("Inserted: syngenta_ventures -> arado (Series A 2023)")
else:
    print("Already exists: syngenta_ventures -> arado")

# ─── 4. syngenta_ventures -> agrolend (Series C, October 2024, ~$55M) ─────────
iid_agrolend = make_iid("syngenta_ventures", "agrolend", "2024-series-c")
existing_ie2 = conn.execute(
    "SELECT investment_id FROM investment_edges WHERE investor_id='syngenta_ventures' AND startup_id='agrolend'"
).fetchone()
if not existing_ie2:
    conn.execute("""
        INSERT INTO investment_edges
        (investment_id, investor_id, startup_id, round_name, round_stage,
         announced_date, amount, currency, is_lead, confidence_score, source_id, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        iid_agrolend,
        "syngenta_ventures", "agrolend",
        "Series C", "series-c",
        "2024-10-18",
        55_000_000, "USD",
        1,  # lead investor
        0.95,
        None,
        "Syngenta Group Ventures CO-LED Series C round of R$300M (~$55M) alongside Creation Investments. Other investors: Vivo Ventures, Nochu Bank, L4/B3 VC arm. Source: tribu.la, Rio Times, Money Times, multiple press.",
    ))
    print("Inserted: syngenta_ventures -> agrolend (Series C 2024, led)")
else:
    print("Already exists: syngenta_ventures -> agrolend")

conn.commit()
print("\nFinal counts:")
print("  investment_edges:", conn.execute("SELECT COUNT(*) FROM investment_edges").fetchone()[0])
print("  support_edges:", conn.execute("SELECT COUNT(*) FROM support_edges").fetchone()[0])
print("  entities:", conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0])
conn.close()
