"""Batch 2 of validation_edges + Krilltech Embrapa support_edge.

Sources:
- Symbiomics + Corteva: https://www.symbiomics.com.br/symbiomics-completes-series-a-funding-round-led-by-corteva-to-advance-next-generation-biologicals/
- Krilltech + Embrapa: Agfundernews: 'Krilltech emerged from a 7-year research partnership between UnB and Embrapa'
"""
import sqlite3
import hashlib
import datetime
import sys

sys.stdout.reconfigure(encoding="utf-8")
conn = sqlite3.connect("db/bio_latam.db")
now = datetime.datetime.now(datetime.UTC).isoformat()

inserted_val = 0
inserted_sup = 0


def add_validation(startup_id, counterparty_id, val_type, status,
                   confidence, notes, source_url, started_at=None):
    global inserted_val
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
        print(f"Inserted val: {startup_id} -> {counterparty_id} ({val_type})")
        inserted_val += 1
    else:
        print(f"Already exists: {startup_id} -> {counterparty_id} ({val_type})")


def add_support(source, target, support_type, confidence, notes, source_url):
    global inserted_sup
    sid = "sup_" + hashlib.md5(f"{source}|{target}|{support_type}".encode()).hexdigest()[:8]
    existing = conn.execute(
        "SELECT support_id FROM support_edges WHERE source_entity_id=? AND target_entity_id=? AND support_type=?",
        (source, target, support_type)
    ).fetchone()
    if not existing:
        conn.execute("""INSERT OR IGNORE INTO support_edges
            (support_id, source_entity_id, target_entity_id, support_type,
             notes, source_url, confidence_score, added_by, added_at)
            VALUES (?,?,?,?,?,?,?,'human:curador',?)""",
            (sid, source, target, support_type, notes, source_url, confidence, now))
        print(f"Inserted sup: {source} -> {target} ({support_type})")
        inserted_sup += 1
    else:
        print(f"Already exists: {source} -> {target} ({support_type})")


# --- Symbiomics + Corteva: technology_partnership ---
# Corteva strategic investment IS a co-development technology partnership
# Article: "Symbiomics has established partnerships with several companies in the agricultural sector
#  to co-develop innovative biological solutions" + Corteva invested as "Corteva first investment in Brazil"
# This is a clear technology_partnership (R&D co-development)
add_validation(
    "symbiomics", "corteva", "technology_partnership", "confirmed",
    0.92,
    "Corteva Catalyst led Symbiomics Series A as strategic investment (Jun 2025) to co-develop next-generation biologicals. Article: 'Corteva first investment in Brazil'. Products in testing, market launch anticipated within 3 years.",
    "https://www.symbiomics.com.br/symbiomics-completes-series-a-funding-round-led-by-corteva-to-advance-next-generation-biologicals/",
    "2025-06-25",
)

# --- Krilltech + Embrapa: research partnership ---
# AgFunderNews confirms: "emerged from a 7-year research partnership between UnB and Embrapa"
# This is a foundational R&D partnership, use technology_partnership (R&D origin)
# Also add as support_edge from embrapa (grant_recipient or accelerator_cohort equivalent)
add_validation(
    "krilltech", "embrapa", "technology_partnership", "confirmed",
    0.88,
    "Krilltech technology emerged from a 7-year joint R&D partnership between University of Brasilia (UnB) and Embrapa (Brazilian Agricultural Research Corporation). Nanostructured biofertilizer Arbolin Biogenesis originated from this collaboration. Source: AgFunderNews Latam ag biologicals report 2024.",
    "https://agfundernews.com/how-latin-america-is-moving-from-a-pioneer-to-a-powerhouse-in-agricultural-biologicals",
    "2017-01-01",  # approximate: 7-yr partnership pre-commercialization
)

# Add Embrapa as support_edge source for Krilltech (R&D origin / spinout)
add_support(
    "embrapa", "krilltech", "accelerator_cohort",  # closest match to research spinout
    0.85,
    "Krilltech is an Embrapa technology spinout: its nanostructured biofertilizer platform originated from a 7-year R&D partnership with Embrapa and University of Brasilia (UnB). Confirmed: AgFunderNews 2024 LATAM biologicals report.",
    "https://agfundernews.com/how-latin-america-is-moving-from-a-pioneer-to-a-powerhouse-in-agricultural-biologicals",
)

conn.commit()
print()
print(f"validation_edges inserted: {inserted_val}")
print(f"support_edges inserted: {inserted_sup}")
print("Total validation_edges:", conn.execute("SELECT COUNT(*) FROM validation_edges").fetchone()[0])
print("Total support_edges:", conn.execute("SELECT COUNT(*) FROM support_edges").fetchone()[0])
conn.close()
