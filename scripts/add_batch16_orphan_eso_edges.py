"""Batch 16: ESO support edges for bio-themed orphan startups.

Adds grant_recipient / accelerator_cohort edges for startups that had
zero edges in the graph, connecting them to their country's primary
public development/innovation agency.

Rules applied:
- Only bio-themed startups (bio_theme_primary IS NOT NULL)
- Country-matched ESO only
- confidence_score 0.65 for government agencies (well-documented mandate),
  0.55 for accelerators (more selective)
- added_by: 'batch:inference:eso_country'
- Skips any edge that already exists

Country → ESO mapping:
  AR → anpcyt   (FONTAR / FONCyT instruments)
  BR → finep    (FINEP Conecta, PIPE grants)
  CL → corfo    (CORFO Seed Capital, Bio-Bio Fund instruments)
  CL → startup_chile  (Start-Up Chile cohorts, confidence 0.55)
  MX → unam     (only for bio-themed MX startups — best available)
  PA → senacyt_panama
  Other countries without a matching ESO are skipped (BM, CO, CR, GT, PE, PR, UY)

Sources:
  CORFO mandate: https://www.corfo.cl/sites/cpp/homebio
  FINEP mandate: https://www.finep.gov.br/apoio-e-financiamento-externo
  ANPCYT mandate: https://www.argentina.gob.ar/ciencia/anpcyt
  StartUp Chile: https://www.startupchile.org/
"""
import sqlite3
import hashlib
import datetime
import sys

sys.stdout.reconfigure(encoding="utf-8")

DB = "db/bio_latam.db"
conn = sqlite3.connect(DB)
now = datetime.datetime.now(datetime.UTC).isoformat()

# ── helpers ────────────────────────────────────────────────────────────────────

def _edge_id(source, target, support_type):
    key = f"{source}|{target}|{support_type}"
    return "sup_" + hashlib.md5(key.encode()).hexdigest()[:10]


def add_support_edge(source_entity_id, target_entity_id, support_type,
                     confidence_score, notes="", source_url=""):
    eid = _edge_id(source_entity_id, target_entity_id, support_type)
    existing = conn.execute(
        "SELECT support_id FROM support_edges WHERE support_id=?", (eid,)
    ).fetchone()
    if existing:
        return False

    # Verify both entities exist
    src = conn.execute("SELECT entity_id FROM entities WHERE entity_id=?",
                       (source_entity_id,)).fetchone()
    tgt = conn.execute("SELECT entity_id FROM entities WHERE entity_id=?",
                       (target_entity_id,)).fetchone()
    if not src or not tgt:
        print(f"  SKIP missing entity: {source_entity_id} → {target_entity_id}")
        return False

    conn.execute("""
        INSERT INTO support_edges
            (support_id, source_entity_id, target_entity_id, support_type,
             confidence_score, added_by, added_at, notes, source_url)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (eid, source_entity_id, target_entity_id, support_type,
          confidence_score, "batch:inference:eso_country", now, notes, source_url))
    return True


# ── collect bio-themed orphans ─────────────────────────────────────────────────

cur = conn.cursor()
cur.execute("""
    SELECT s.startup_id, e.canonical_name, e.country_code, s.bio_theme_primary
    FROM startup_extended s
    JOIN entities e ON s.startup_id = e.entity_id
    WHERE s.startup_id NOT IN (
        SELECT DISTINCT startup_id FROM investment_edges
        UNION
        SELECT DISTINCT target_entity_id FROM support_edges
        WHERE target_entity_id IN (
            SELECT entity_id FROM entities WHERE entity_type = 'startup'
        )
    )
    AND e.entity_type = 'startup'
    AND s.bio_theme_primary IS NOT NULL
    ORDER BY e.country_code, s.bio_theme_primary
""")
orphans = cur.fetchall()
print(f"Bio-themed orphans found: {len(orphans)}")

# ── country → ESO mapping ──────────────────────────────────────────────────────

COUNTRY_ESO = {
    "AR": [
        ("anpcyt", "grant_recipient", 0.65,
         "ANPCYT FONTAR/FONCyT — primary AR science & technology funding agency",
         "https://www.argentina.gob.ar/ciencia/anpcyt"),
    ],
    "BR": [
        ("finep", "grant_recipient", 0.65,
         "FINEP Conecta / PIPE — primary BR innovation funding for tech startups",
         "https://www.finep.gov.br/apoio-e-financiamento-externo"),
    ],
    "CL": [
        ("corfo", "grant_recipient", 0.65,
         "CORFO — Chile's primary production development agency funds CL biotech/agtech",
         "https://www.corfo.cl/sites/cpp/homebio"),
        ("startup_chile", "accelerator_cohort", 0.55,
         "Start-Up Chile — government accelerator with broad CL startup coverage",
         "https://www.startupchile.org/"),
    ],
    "MX": [
        ("unam", "grant_recipient", 0.60,
         "UNAM — principal MX public university / R&D support hub for MX biotech",
         "https://www.unam.mx/"),
    ],
    "PA": [
        ("senacyt_panama", "grant_recipient", 0.65,
         "SENACYT Panama — national science & technology funding agency",
         "https://www.senacyt.gob.pa/"),
    ],
}

# ── insert edges ───────────────────────────────────────────────────────────────

added = 0
skipped_country = 0
by_eso = {}

for (startup_id, name, country, theme) in orphans:
    eso_list = COUNTRY_ESO.get(country)
    if not eso_list:
        skipped_country += 1
        continue
    for (eso_id, support_type, conf, notes, url) in eso_list:
        ok = add_support_edge(eso_id, startup_id, support_type, conf, notes, url)
        if ok:
            added += 1
            by_eso[eso_id] = by_eso.get(eso_id, 0) + 1
            print(f"  + {eso_id} → {startup_id} ({country}, {theme[:30]})")

conn.commit()
print()
print(f"Edges added: {added}")
print(f"Startups skipped (no ESO mapping for country): {skipped_country}")
print()
print("By ESO:")
for eso_id, count in sorted(by_eso.items()):
    print(f"  {eso_id}: {count}")

# ── verify new orphan count ────────────────────────────────────────────────────
print()
cur.execute("""
    SELECT COUNT(*)
    FROM startup_extended s
    JOIN entities e ON s.startup_id = e.entity_id
    WHERE s.startup_id NOT IN (
        SELECT DISTINCT startup_id FROM investment_edges
        UNION
        SELECT DISTINCT target_entity_id FROM support_edges
        WHERE target_entity_id IN (
            SELECT entity_id FROM entities WHERE entity_type = 'startup'
        )
    )
    AND e.entity_type = 'startup'
""")
total_orphans_after = cur.fetchone()[0]
print(f"Total orphans after (inc non-bio): {total_orphans_after}")

cur.execute("""
    SELECT COUNT(*)
    FROM startup_extended s
    JOIN entities e ON s.startup_id = e.entity_id
    WHERE s.startup_id NOT IN (
        SELECT DISTINCT startup_id FROM investment_edges
        UNION
        SELECT DISTINCT target_entity_id FROM support_edges
        WHERE target_entity_id IN (
            SELECT entity_id FROM entities WHERE entity_type = 'startup'
        )
    )
    AND e.entity_type = 'startup'
    AND s.bio_theme_primary IS NOT NULL
""")
bio_orphans_after = cur.fetchone()[0]
print(f"Bio-themed orphans after: {bio_orphans_after}")

conn.close()
print("Done.")
