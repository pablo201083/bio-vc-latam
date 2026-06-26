"""
scripts/_clean_db_summaries.py — Limpia frases meta de curación de startup_summary_v1 en la DB.
Aplica los mismos patrones que se usaron para limpiar el CSV maestro.
"""
import sqlite3
import re
import pathlib
import sys

DB = pathlib.Path(__file__).resolve().parent.parent / "db" / "bio_latam.db"

META_PATTERNS = [
    re.compile(r'\s*It belongs inside BIO VC LATAM[^.]*\.', re.IGNORECASE),
    re.compile(r'\s*It is a core BIO VC LATAM[^.]*\.', re.IGNORECASE),
    re.compile(r'\s*It should remain outside BIO VC LATAM[^.]*\.', re.IGNORECASE),
    re.compile(r'\s*making it a core[^.]*company\.', re.IGNORECASE),
    re.compile(r'\s*The company belongs inside BIO VC LATAM[^.]*\.', re.IGNORECASE),
    re.compile(r'\s*Entra en tesis por[^.]*\.', re.IGNORECASE),
    re.compile(r'\s*Queda fuera de tesis por[^.]*\.', re.IGNORECASE),
    re.compile(r'\s*Entra en tesis como[^.]*\.', re.IGNORECASE),
    # Mid-paragraph scope analysis sentences (with or without trailing period — some are truncated)
    re.compile(r'\s*It is (?:not|a border case|excluded)[^.]*BIO VC LATAM[^.]*\.?', re.IGNORECASE),
    re.compile(r'\s*It should (?:stay|remain)[^.]*BIO VC LATAM[^.]*\.?', re.IGNORECASE),
    re.compile(r'\s*it belongs inside the broader BIO VC LATAM[^.]*\.?', re.IGNORECASE),
    re.compile(r'\s*[Ii]ts BIO VC LATAM[^.]*\.?', re.IGNORECASE),
    re.compile(r'\s*[^.]*BIO VC LATAM[^.]*thesis[^.]*\.?', re.IGNORECASE),
    re.compile(r'\s*[^.]*BIO VC LATAM[^.]*perimeter[^.]*\.?', re.IGNORECASE),
    re.compile(r'\s*It should cluster with[^.]*\.?', re.IGNORECASE),
    re.compile(r'\s*The company belongs inside BIO VC LATAM[^.]*\.?$', re.IGNORECASE),
    re.compile(r'\s*It is a core BIO VC LATAM[^.]*\.?$', re.IGNORECASE),
]

conn = sqlite3.connect(DB)

for field in ("startup_summary_v1", "startup_summary_en"):
    rows = conn.execute(
        f"SELECT startup_id, {field} FROM startup_extended WHERE {field} IS NOT NULL"
    ).fetchall()
    updates = []
    for sid, v1 in rows:
        text = v1
        for pat in META_PATTERNS:
            text = pat.sub('', text).strip()
        if text != v1:
            updates.append((text, sid))
    print(f"{field}: {len(updates)} rows to update")
    conn.executemany(f"UPDATE startup_extended SET {field}=? WHERE startup_id=?", updates)
    conn.commit()

remaining_v1 = conn.execute(
    "SELECT count(*) FROM startup_extended WHERE startup_summary_v1 LIKE '%BIO VC LATAM%'"
).fetchone()[0]
remaining_en = conn.execute(
    "SELECT count(*) FROM startup_extended WHERE startup_summary_en LIKE '%BIO VC LATAM%'"
).fetchone()[0]
print(f"Remaining v1: {remaining_v1} | en: {remaining_en}")
conn.close()
print("Done.")
