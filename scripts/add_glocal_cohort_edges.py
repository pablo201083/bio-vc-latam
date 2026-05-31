"""Add GLOCAL Game Changers 2024 cohort participation edges."""
import sqlite3
import hashlib
import datetime
import sys

sys.stdout.reconfigure(encoding="utf-8")
conn = sqlite3.connect("db/bio_latam.db")
now = datetime.datetime.now(datetime.UTC).isoformat()

SOURCE_URL = "https://agfundernews.com/meet-the-10-agrifoodtech-startups-chosen-to-pitch-at-glocals-game-changers-2024"
NOTE_TEMPLATE = "GLOCAL Game Changers 2024 pitch finalist - one of 10 agrifoodtech startups chosen to pitch at GLOCAL's annual accelerator event (access to up to $500K investment)"


def make_sid(a, b):
    return "glocal_gc24_" + hashlib.md5((a + "|" + b).encode()).hexdigest()[:8]


# GLOCAL Game Changers 2024 finalists confirmed in our DB
# Source: agfundernews.com article listing all 10 startups
cohort_rows = [
    # (source, target, note)
    ("glocal", "calice_biotech", "GLOCAL Game Changers 2024 - gene editing for cannabis cultivars; one of 10 finalists"),
    ("glocal", "zavia_bio",      "GLOCAL Game Changers 2024 - ag biotechnology (AR); one of 10 finalists"),
    ("glocal", "bemagro",        "GLOCAL Game Changers 2024 - farm management software (BR); one of 10 finalists"),
    ("glocal", "blooms",         "GLOCAL Game Changers 2024 - ag fintech for LATAM produce exporters (MX); one of 10 finalists"),
]

inserted = 0
for src, tgt, note in cohort_rows:
    sid = make_sid(src, tgt)
    existing = conn.execute(
        "SELECT support_id FROM support_edges WHERE source_entity_id=? AND target_entity_id=? AND support_type='cohort_participant'",
        (src, tgt)
    ).fetchone()
    if not existing:
        conn.execute("""
            INSERT OR IGNORE INTO support_edges
            (support_id, source_entity_id, target_entity_id, support_type,
             notes, source_url, confidence_score, added_by, added_at)
            VALUES (?,?,?,?,?,?,?,"human:curador",?)
        """, (sid, src, tgt, "cohort_participant", note, SOURCE_URL, 0.78, now))
        print(f"Inserted: {src} -> {tgt} (cohort_participant)")
        inserted += 1
    else:
        print(f"Already exists: {src} -> {tgt}")

conn.commit()
print(f"\nInserted {inserted} support edges")
print("Total support_edges:", conn.execute("SELECT COUNT(*) FROM support_edges").fetchone()[0])
conn.close()
