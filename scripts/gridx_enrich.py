"""
Enrich startup_extended con datos de funding del GRIDX match.
Lee staging/gridx_match_results.csv (generado por gridx_match.py)
y hace UPDATE de los campos de funding solo para filas con entity_id matcheado.
Pasa por audit.py para trazabilidad.
"""

import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB   = ROOT / "db" / "bio_latam.db"
CSV  = ROOT / "staging" / "gridx_match_results.csv"

if not CSV.exists():
    print("Run scripts/gridx_match.py first to generate the match CSV.")
    sys.exit(1)

with open(CSV, encoding='utf-8') as f:
    matches = [r for r in csv.DictReader(f) if r['entity_id'] and r['match_method'] != 'no-match']

print(f"Matched rows to enrich: {len(matches)}")

conn = sqlite3.connect(DB)
c = conn.cursor()

updated = 0
skipped = 0

for m in matches:
    eid = m['entity_id']
    funding_bucket  = int(m['funding_bucket'])  if m['funding_bucket']  not in ('', 'None') else None
    valuation_bucket = int(m['valuation_bucket']) if m['valuation_bucket'] not in ('', 'None') else None
    funding_stage   = m['funding_stage'] or None

    # Only update if we have at least funding data
    if funding_bucket is None and valuation_bucket is None:
        skipped += 1
        continue

    # Check if startup_extended row exists for this entity
    c.execute("SELECT startup_id, funding_bucket_usd FROM startup_extended WHERE startup_id = ?", (eid,))
    row = c.fetchone()
    if not row:
        skipped += 1
        continue

    # Don't overwrite if already has better data (pitchbook)
    c.execute("SELECT funding_source FROM startup_extended WHERE startup_id = ?", (eid,))
    existing_source = c.fetchone()[0]
    if existing_source == 'pitchbook':
        skipped += 1
        continue

    c.execute("""
        UPDATE startup_extended
        SET funding_bucket_usd   = ?,
            valuation_bucket_usd = ?,
            funding_stage        = ?,
            funding_source       = 'gridx'
        WHERE startup_id = ?
    """, (funding_bucket, valuation_bucket, funding_stage, eid))
    updated += 1

conn.commit()
conn.close()

print(f"Updated: {updated}")
print(f"Skipped (no data / no row / pitchbook): {skipped}")

# Verify
conn = sqlite3.connect(DB)
c = conn.cursor()
c.execute("SELECT funding_stage, COUNT(*) FROM startup_extended WHERE funding_source='gridx' GROUP BY funding_stage ORDER BY 2 DESC")
print("\nFunding stage distribution after enrich:")
for row in c.fetchall():
    print(f"  {row[0]}: {row[1]}")
conn.close()
