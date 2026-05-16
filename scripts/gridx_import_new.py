"""
Importa las compañías del GRIDX que NO están en entities.
Crea filas en `entities` (status='unprocessed') y en `startup_extended`
(scope_decision='review') con los datos que tenemos del Excel.
No modifica ninguna entidad existente.
"""

import csv
import re
import sqlite3
import sys
import openpyxl
from pathlib import Path
from datetime import date

ROOT = Path(__file__).parent.parent
XLS  = Path(r"F:\Downloads\Analisis GRIDX Deeptech Nueva Ola .xlsx")
DB   = ROOT / "db" / "bio_latam.db"
CSV  = ROOT / "staging" / "gridx_match_results.csv"

COUNTRY_CODE = {
    "Argentina": "AR", "Brazil": "BR", "Chile": "CL", "Mexico": "MX",
    "Colombia": "CO", "Peru": "PE", "Uruguay": "UY", "Costa Rica": "CR",
    "Guatemala": "GT", "Panama": "PA", "Nicaragua": "NI", "Bolivia": "BO",
    "Ecuador": "EC", "Venezuela": "VE", "Paraguay": "PY", "Cuba": "CU",
    "Dominican Republic": "DO", "Puerto Rico": "PR", "Honduras": "HN",
    "El Salvador": "SV", "Bahamas": "BS", "Bermuda": "BM",
}

FUNDING_TIERS = {
    0:    "pre-seed", 1: "seed", 5: "series-a", 10: "series-a",
    15:   "series-a", 25: "series-b", 100: "series-c+", 500: "growth", 1000: "growth",
}

def slugify(name):
    s = name.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_-]+', '_', s)
    s = re.sub(r'^_|_$', '', s)
    return s[:64]

def parse_bucket(val):
    if val is None: return None
    if isinstance(val, (int, float)): return int(val)
    s = str(val).strip()
    if s.startswith("<"): return 0
    if s.startswith("#") or s == "": return None
    try: return int(float(s))
    except: return None

# ── Load full GRIDX data ───────────────────────────────────────────────────────
wb = openpyxl.load_workbook(XLS, data_only=True)
ws = wb.active
gridx_full = {}
for row in ws.iter_rows(values_only=True):
    company = row[0]
    if not company or not isinstance(company, str) or company == 'Company':
        continue
    gridx_full[company] = {
        'sector':    str(row[2] or ''),
        'subsector': str(row[3] or ''),
        'new_biotech': bool(row[5]),
        'description': (row[11] or '')[:800],
        'web': str(row[12]).strip() if row[12] else None,
        'founded': int(float(row[9])) if row[9] and str(row[9]).strip() not in ('N/A','') else None,
        'country': row[8],
        'funding_raw':   row[6],
        'valuation_raw': row[7],
    }

# ── Load unmatched companies ───────────────────────────────────────────────────
with open(CSV, encoding='utf-8') as f:
    unmatched = [r for r in csv.DictReader(f) if r['match_method'] == 'no-match']

print(f"Unmatched to import: {len(unmatched)}")

# ── Connect DB ─────────────────────────────────────────────────────────────────
conn = sqlite3.connect(DB)
c = conn.cursor()

# Build existing entity_id set to avoid collisions
c.execute("SELECT entity_id FROM entities")
existing_ids = {r[0] for r in c.fetchall()}

today = date.today().isoformat()
inserted_entities = 0
inserted_extended = 0
skipped = 0

for r in unmatched:
    name = r['gridx_company']
    g = gridx_full.get(name, {})

    # Generate unique entity_id
    base_slug = slugify(name)
    slug = base_slug
    counter = 2
    while slug in existing_ids:
        slug = f"{base_slug}_{counter}"
        counter += 1

    country_name = g.get('country') or r.get('country') or ''
    country_code = COUNTRY_CODE.get(country_name, '')

    website = g.get('web') or r.get('gridx_web') or None
    # Normalize website
    if website and not website.startswith('http'):
        website = 'https://' + website

    founded = g.get('founded')
    description = g.get('description') or ''

    funding_bucket  = parse_bucket(g.get('funding_raw'))
    valuation_bucket = parse_bucket(g.get('valuation_raw'))
    funding_stage   = FUNDING_TIERS.get(funding_bucket)

    # ── Insert into entities ───────────────────────────────────────────────────
    try:
        c.execute("""
            INSERT INTO entities
              (entity_id, entity_type, canonical_name, slug, short_description,
               country_code, website, status, founded_year, last_verified_at)
            VALUES (?, 'startup', ?, ?, ?, ?, ?, 'unprocessed', ?, ?)
        """, (slug, name, slug, description[:300] or None,
              country_code or None, website, founded, today))
        existing_ids.add(slug)
        inserted_entities += 1
    except sqlite3.IntegrityError as e:
        print(f"  SKIP entity {name}: {e}")
        skipped += 1
        continue

    # ── Insert into startup_extended ───────────────────────────────────────────
    sector_tag = g.get('sector', '')
    try:
        c.execute("""
            INSERT INTO startup_extended
              (startup_id, scope_decision, scope_status, scope_reason,
               business_one_liner,
               funding_bucket_usd, valuation_bucket_usd, funding_stage, funding_source,
               data_quality_score, quality_band)
            VALUES (?, 'review', 'pending_curation', 'gridx_import',
                    ?,
                    ?, ?, ?, 'gridx',
                    0.0, 'low')
        """, (slug,
              description[:200] or None,
              funding_bucket, valuation_bucket, funding_stage))
        inserted_extended += 1
    except sqlite3.IntegrityError as e:
        print(f"  SKIP extended {name}: {e}")

conn.commit()
conn.close()

print(f"\nResult:")
print(f"  entities inserted:         {inserted_entities}")
print(f"  startup_extended inserted: {inserted_extended}")
print(f"  skipped (collision):       {skipped}")
print(f"\nNew entities have status='unprocessed', scope_decision='review'.")
print("Run pipeline.py rebuild --phase canonical to re-classify.")
