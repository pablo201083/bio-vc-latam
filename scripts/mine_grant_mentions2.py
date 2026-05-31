"""
More precise mining — verify context around each match.
"""
import sqlite3
import re
import sys
sys.stdout.reconfigure(encoding="utf-8")

conn = sqlite3.connect("db/bio_latam.db")

# Check the Chilean CORFO candidates more precisely
CORFO_IDS = ["huiro", "innovai", "matchetune", "neocrop-technologies", "patagon-fiber"]

print("=== Verifying CORFO snippet context ===")
for sid in CORFO_IDS:
    row = conn.execute("""
        SELECT se.startup_id, se.startup_summary_v1, se.startup_summary_en
        FROM startup_extended se
        WHERE se.startup_id = ?
    """, (sid,)).fetchone()
    if not row:
        print(f"  {sid}: NOT FOUND")
        continue
    text = " ".join(filter(None, [row[1], row[2]]))
    # Find relevant sentence
    sentences = re.split(r'[.!?]', text)
    for s in sentences:
        if re.search(r"CORFO|Start.Up Chile|Startup Chile", s, re.IGNORECASE):
            print(f"\n  {sid}:")
            print(f"    MATCH: {s.strip()}")
    # Also look for any funding/grant context
    for s in sentences:
        if re.search(r"fund|grant|subsidio|adjudic|apoya|financ|ANID|CONICYT|beca|concurso", s, re.IGNORECASE):
            print(f"    FUNDING CONTEXT: {s.strip()[:120]}")

print("\n=== calice-ai-ar full summary (Corteva/Syngenta context) ===")
row = conn.execute("SELECT startup_summary_v1, startup_summary_en FROM startup_extended WHERE startup_id='calice-ai-ar'").fetchone()
if row:
    text = " ".join(filter(None, list(row)))
    sentences = re.split(r'[.!?]', text)
    for s in sentences:
        if re.search(r"Corteva|Syngenta|customer|pilot|partner|client", s, re.IGNORECASE):
            print(f"  {s.strip()[:160]}")

print("\n=== All startups mentioning ANPCYT/FONTAR explicitly ===")
for row in conn.execute("""
    SELECT se.startup_id, e.canonical_name, e.country_code
    FROM startup_extended se
    JOIN entities e ON se.startup_id = e.entity_id
    WHERE (se.startup_summary_v1 LIKE '%ANPCyT%' OR se.startup_summary_v1 LIKE '%FONTAR%'
        OR se.startup_summary_en LIKE '%ANPCyT%' OR se.startup_summary_en LIKE '%FONTAR%'
        OR se.startup_summary_v1 LIKE '%ANPCYT%' OR se.startup_summary_v1 LIKE '%FONCyT%')
"""):
    print(f"  {row[0]} ({row[2]}) — {row[1]}")
    # Get the matching sentence
    d = conn.execute("SELECT startup_summary_v1, startup_summary_en FROM startup_extended WHERE startup_id=?", (row[0],)).fetchone()
    text = " ".join(filter(None, list(d)))
    for s in re.split(r'[.!?]', text):
        if re.search(r"ANPCyT|FONTAR|FONCyT|ANPCYT", s, re.IGNORECASE):
            print(f"    -> {s.strip()[:160]}")

print("\n=== All startups mentioning FINEP explicitly ===")
for row in conn.execute("""
    SELECT se.startup_id, e.canonical_name, e.country_code
    FROM startup_extended se
    JOIN entities e ON se.startup_id = e.entity_id
    WHERE se.startup_summary_v1 LIKE '%FINEP%' OR se.startup_summary_en LIKE '%FINEP%'
"""):
    print(f"  {row[0]} ({row[2]}) — {row[1]}")
    d = conn.execute("SELECT startup_summary_v1, startup_summary_en FROM startup_extended WHERE startup_id=?", (row[0],)).fetchone()
    text = " ".join(filter(None, list(d)))
    for s in re.split(r'[.!?]', text):
        if re.search(r"FINEP", s, re.IGNORECASE):
            print(f"    -> {s.strip()[:160]}")

print("\n=== All startups mentioning Embrapa explicitly ===")
for row in conn.execute("""
    SELECT se.startup_id, e.canonical_name, e.country_code
    FROM startup_extended se
    JOIN entities e ON se.startup_id = e.entity_id
    WHERE se.startup_summary_v1 LIKE '%Embrapa%' OR se.startup_summary_en LIKE '%Embrapa%'
       OR se.startup_summary_v1 LIKE '%EMBRAPA%' OR se.startup_summary_en LIKE '%EMBRAPA%'
"""):
    print(f"  {row[0]} ({row[2]}) — {row[1]}")
    d = conn.execute("SELECT startup_summary_v1, startup_summary_en FROM startup_extended WHERE startup_id=?", (row[0],)).fetchone()
    text = " ".join(filter(None, list(d)))
    for s in re.split(r'[.!?]', text):
        if re.search(r"embrapa", s, re.IGNORECASE):
            print(f"    -> {s.strip()[:160]}")
