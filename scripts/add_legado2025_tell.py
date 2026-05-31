"""Add Bayer Legado 2025 winner: Tell (speech neurodegeneration detection)"""
import sqlite3
import hashlib
import datetime
import sys

sys.stdout.reconfigure(encoding="utf-8")
conn = sqlite3.connect("db/bio_latam.db")
now = datetime.datetime.now(datetime.UTC).isoformat()

# tell in DB = AR country, speech-based neurodegeneration detection
# Bayer Legado 2025 winner = "Tell Biomarkers (UY)" - voice analysis for neurodegeneration
# Description matches perfectly; country discrepancy (AR vs UY) is likely a data issue
# Confidence: 0.82 (description match strong, slight country uncertainty)

sid = "bayer25_" + hashlib.md5("bayer_crop|tell".encode()).hexdigest()[:8]
existing = conn.execute(
    "SELECT support_id FROM support_edges WHERE source_entity_id='bayer_crop' AND target_entity_id='tell' AND support_type='cohort_participant'"
).fetchone()

if not existing:
    conn.execute("""
        INSERT OR IGNORE INTO support_edges
        (support_id, source_entity_id, target_entity_id, support_type,
         notes, source_url, confidence_score, added_by, added_at)
        VALUES (?,?,?,?,?,?,?,"human:curador",?)
    """, (
        sid, "bayer_crop", "tell",
        "cohort_participant",
        "Bayer Legado 2025 winner - Tell Biomarkers: AI + voice analysis for early detection of neurodegenerative diseases. Description matches DB 'Tell' (speech-based neurodegeneration detection). Country discrepancy: DB=AR, Legado=UY. Confidence 0.82.",
        "https://www.infobae.com/economia/networking/2025/08/18/legado-2025-se-anunciaron-los-ganadores-del-premio-a-la-innovacion-social-con-impacto-de-bayer/",
        0.82,
        now,
    ))
    print("Inserted: bayer_crop -> tell (cohort_participant, Legado 2025)")
else:
    print("Already exists: bayer_crop -> tell")

conn.commit()
print("Total support_edges:", conn.execute("SELECT COUNT(*) FROM support_edges").fetchone()[0])
conn.close()
