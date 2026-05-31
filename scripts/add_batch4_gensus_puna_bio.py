"""Batch 4: Gensus entity + Bioheuris-Gensus validation, Puna Bio updates.

Sources:
- Bioheuris+Gensus: https://www.prnewswire.com/news-releases/argentine-companies-gensus-and-bioheuris-to-develop-non-gmo-herbicide-resistant-cotton-using-gene-editing-301287991.html
  Announced May 11, 2021
- Puna Bio Series A: https://www.prnewswire.com/news-releases/puna-bio-receives-investment-from-corteva-catalyst-302433659.html
  April 22, 2025 - $16.8M Series A led by Corteva Catalyst
"""
import sqlite3
import hashlib
import datetime
import sys

sys.stdout.reconfigure(encoding="utf-8")
conn = sqlite3.connect("db/bio_latam.db")
now = datetime.datetime.now(datetime.UTC).isoformat()


def add_entity(entity_id, entity_type, name, slug, desc, country, website, status):
    existing = conn.execute("SELECT entity_id FROM entities WHERE entity_id=?", (entity_id,)).fetchone()
    if not existing:
        conn.execute("""INSERT INTO entities
            (entity_id, entity_type, canonical_name, slug, short_description,
             country_code, website, status, last_verified_at)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (entity_id, entity_type, name, slug, desc, country, website, status, now))
        print(f"Inserted entity: {entity_id}")
        return True
    else:
        print(f"Already exists: {entity_id}")
        return False


def add_validation(startup_id, counterparty_id, val_type, status,
                   confidence, notes, source_url, started_at=None):
    vid = "val-" + hashlib.md5(f"{startup_id}|{counterparty_id}|{val_type}".encode()).hexdigest()[:12]
    existing = conn.execute(
        "SELECT validation_id FROM validation_edges WHERE startup_id=? AND counterparty_entity_id=? AND validation_type=?",
        (startup_id, counterparty_id, val_type)
    ).fetchone()
    if not existing:
        conn.execute("""INSERT INTO validation_edges
            (validation_id, startup_id, counterparty_entity_id, validation_type,
             started_at, status, confidence_score, notes, source_url, added_by, added_at)
            VALUES (?,?,?,?,?,?,?,?,?,'human:curador',?)""",
            (vid, startup_id, counterparty_id, val_type,
             started_at, status, confidence, notes, source_url, now))
        print(f"Inserted validation: {startup_id} -> {counterparty_id} ({val_type})")
        return True
    else:
        print(f"Already exists: {startup_id} -> {counterparty_id} ({val_type})")
        return False


# ============================================================
# 1. Gensus entity (Argentine cotton seed company)
# ============================================================
add_entity(
    "gensus", "corporate",
    "Gensus SA", "gensus-sa",
    "Argentine cotton seed company (Chaco province) developing improved cotton varieties; partner with Bioheuris for non-GMO CRISPR herbicide-tolerant cotton development.",
    "AR", "https://www.gensus.com.ar", "active",
)

# ============================================================
# 2. Bioheuris + Gensus technology_partnership
# ============================================================
add_validation(
    "bioheuris", "gensus", "technology_partnership", "confirmed",
    0.92,
    "Bioheuris and Gensus announced May 2021 partnership to develop non-GMO herbicide-tolerant cotton using CRISPR gene editing. Bioheuris provides the gene editing platform (enhancing crop's own genes, no foreign DNA); Gensus provides cotton seed varieties and breeding know-how. Patent application filed with USPTO.",
    "https://www.prnewswire.com/news-releases/argentine-companies-gensus-and-bioheuris-to-develop-non-gmo-herbicide-resistant-cotton-using-gene-editing-301287991.html",
    "2021-05-11",
)

# ============================================================
# 3. Update Puna Bio Corteva Catalyst investment edge
#    (previously had no amount or correct date)
# ============================================================
# Series A: $16.8M led by Corteva Catalyst (Apr 22, 2025)
# Also participating: AIR Capital, GLOCAL, SP Ventures (already in DB)
existing_edge = conn.execute(
    "SELECT investment_id FROM investment_edges WHERE investor_id='corteva_catalyst' AND startup_id='puna_bio' AND round_stage='series-a'"
).fetchone()
if existing_edge:
    conn.execute("""UPDATE investment_edges
        SET amount=16800000, currency='USD', announced_date='2025-04-22',
            confidence_score=0.98, is_lead=1,
            notes='Corteva Catalyst LED Puna Bio $16.8M Series A (Apr 22, 2025). Corteva provides global distribution network to scale Kunza + Kanzama bioinoculants in US, Brazil, Paraguay. 800K+ acres already treated in 3 commercial seasons. Source: PRNewswire official release.'
        WHERE investment_id=?""",
        (existing_edge[0],))
    print("Updated: corteva_catalyst -> puna_bio (series-a): amount=$16.8M, date=2025-04-22")
else:
    print("Not found: corteva_catalyst -> puna_bio (series-a)")

# ============================================================
# 4. Puna Bio + Corteva: technology_partnership (distribution)
# ============================================================
# "Corteva's global distribution networks will accelerate Puna Bio's entry into the U.S., Brazil, and Paraguay"
# This is a commercial distribution / technology_partnership
add_validation(
    "puna_bio", "corteva", "technology_partnership", "confirmed",
    0.92,
    "Corteva Catalyst led Puna Bio's $16.8M Series A (Apr 2025) with commercial distribution partnership: Corteva's global distribution networks will accelerate Puna Bio's products (Kunza, Kanzama bioinoculants) into US, Brazil, and Paraguay. Regulatory approvals underway; US trials starting 2025.",
    "https://www.prnewswire.com/news-releases/puna-bio-receives-investment-from-corteva-catalyst-302433659.html",
    "2025-04-22",
)

conn.commit()
print()
print("Total entities:", conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0])
print("Total validation_edges:", conn.execute("SELECT COUNT(*) FROM validation_edges").fetchone()[0])

# Verify Bioheuris edges
print()
print("=== Bioheuris edges ===")
for r in conn.execute("SELECT startup_id, counterparty_entity_id, validation_type FROM validation_edges WHERE startup_id='bioheuris'"):
    print(f"  val: {r}")

print()
print("=== Puna Bio Series A ===")
for r in conn.execute("SELECT investor_id, round_stage, amount, announced_date FROM investment_edges WHERE startup_id='puna_bio' AND round_stage='series-a'"):
    print(f"  {r}")
for r in conn.execute("SELECT startup_id, counterparty_entity_id, validation_type FROM validation_edges WHERE startup_id='puna_bio'"):
    print(f"  val: {r}")
conn.close()
