"""
derive_secondary_themes.py
--------------------------
Deriva bio_theme_secondary para los startups en el mapa semantico que no tienen
uno asignado. Usa patrones existentes en la DB (cluster+primary->secondary mas
comun) y una tabla de fallbacks por conocimiento del dominio.

Solo aplica a startups con cluster_id >= 0 y bio_theme_secondary vacio.
NO sobreescribe secondaries ya asignados (curados manualmente).

Ejecutar:
  .venv/Scripts/python.exe derive_secondary_themes.py
  .venv/Scripts/python.exe derive_secondary_themes.py --dry-run
"""

import sqlite3, pathlib, datetime, sys, argparse
from collections import defaultdict, Counter

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

parser = argparse.ArgumentParser()
parser.add_argument('--dry-run', action='store_true')
args = parser.parse_args()

DB = pathlib.Path('db/bio_latam.db')
conn = sqlite3.connect(DB)
cur  = conn.cursor()
now  = datetime.datetime.now(datetime.UTC).isoformat()

# ── Build lookup from existing data ──────────────────────────────────────────
# For each (cluster_id, primary), pick most common secondary (excluding same-as-primary)
cur.execute('''SELECT cluster_id, bio_theme_primary, bio_theme_secondary, COUNT(*) n
FROM startup_extended
WHERE cluster_id >= 0
  AND bio_theme_secondary IS NOT NULL AND bio_theme_secondary != ''
  AND bio_theme_secondary != bio_theme_primary
GROUP BY cluster_id, bio_theme_primary, bio_theme_secondary
ORDER BY cluster_id, bio_theme_primary, n DESC''')
rows = cur.fetchall()

# key: (cluster_id, primary) → best secondary (highest n, first encountered)
DATA_LOOKUP = {}
for cl_id, primary, secondary, n in rows:
    key = (cl_id, primary)
    if key not in DATA_LOOKUP:
        DATA_LOOKUP[key] = secondary

# ── Hardcoded fallbacks for cluster+primary combos without existing data ─────
# Based on domain knowledge of the bio-economy taxonomy and cluster semantics
FALLBACK = {
    # CL0 Diagnostics — any primary without data → Therapeutics
    (0, 'Therapeutics'):                          'Diagnostics & Health Access',
    (0, 'Farm Intelligence'):                     'Diagnostics & Health Access',
    (0, 'Bioinputs & Crop Resilience'):           'Diagnostics & Health Access',
    (0, 'Biomanufacturing & Fermentation Economy'): 'Diagnostics & Health Access',

    # CL1 Fish / Aquaculture
    (1, 'Bioinputs & Crop Resilience'):           'Food Systems & Alt Proteins',
    (1, 'Food Systems & Alt Proteins'):           'Nature & Ecosystem Tech',
    (1, 'Biomanufacturing & Fermentation Economy'): 'Food Systems & Alt Proteins',
    (1, 'Nature & Ecosystem Tech'):               'Food Systems & Alt Proteins',
    (1, 'Biomaterials & Circular Economy'):       'Food Systems & Alt Proteins',

    # CL2 Biomaterials — Biobased Chemistry
    (2, 'Biomaterials & Circular Economy'):       'Nature & Ecosystem Tech',
    (2, 'Nature & Ecosystem Tech'):               'Biomaterials & Circular Economy',

    # CL3 Biomaterials — Packaging (no secondary data at all)
    (3, 'Biomaterials & Circular Economy'):       'Nature & Ecosystem Tech',
    (3, 'Biomanufacturing & Fermentation Economy'): 'Biomaterials & Circular Economy',
    (3, 'Nature & Ecosystem Tech'):               'Biomaterials & Circular Economy',
    (3, 'Food Systems & Alt Proteins'):           'Biomaterials & Circular Economy',

    # CL4 Nature — Energy
    (4, 'Nature & Ecosystem Tech'):               'Biomaterials & Circular Economy',
    (4, 'Biomaterials & Circular Economy'):       'Nature & Ecosystem Tech',

    # CL5 Biomanufacturing — Precision Fermentation
    (5, 'Biomanufacturing & Fermentation Economy'): 'Therapeutics',

    # CL6 Food — Novel Ingredients
    (6, 'Food Systems & Alt Proteins'):           'Biomaterials & Circular Economy',
    (6, 'Bioinputs & Crop Resilience'):           'Food Systems & Alt Proteins',
    (6, 'Therapeutics'):                          'Food Systems & Alt Proteins',
    (6, 'Biomaterials & Circular Economy'):       'Food Systems & Alt Proteins',

    # CL7 Therapeutics — Biopharmaceutical
    (7, 'Therapeutics'):                          'Biomaterials & Circular Economy',
    (7, 'Biomanufacturing & Fermentation Economy'): 'Therapeutics',

    # CL8 Therapeutics — Drug Testing
    (8, 'Therapeutics'):                          'Diagnostics & Health Access',

    # CL9 Bioinputs — Seed Treatment
    (9, 'Bioinputs & Crop Resilience'):           'Nature & Ecosystem Tech',

    # CL10 Biomaterials — Antimicrobial (no secondary data)
    (10, 'Biomaterials & Circular Economy'):      'Therapeutics',
    (10, 'Therapeutics'):                         'Diagnostics & Health Access',
    (10, 'Nature & Ecosystem Tech'):              'Biomaterials & Circular Economy',

    # CL11 Bioinputs — Biologicals Crop
    (11, 'Bioinputs & Crop Resilience'):          'Nature & Ecosystem Tech',

    # CL12 Bioinputs — Crop Protection (no secondary data)
    (12, 'Bioinputs & Crop Resilience'):          'Nature & Ecosystem Tech',
    (12, 'Nature & Ecosystem Tech'):              'Bioinputs & Crop Resilience',

    # CL13 Nature — Satellite
    (13, 'Nature & Ecosystem Tech'):              'Farm Intelligence',

    # CL14 Nature — Nature Finance (no secondary data)
    (14, 'Nature & Ecosystem Tech'):              'Farm Intelligence',
    (14, 'Farm Intelligence'):                    'Nature & Ecosystem Tech',

    # CL15 Diagnostics — Device / Nanomedicine
    (15, 'Diagnostics & Health Access'):          'Therapeutics',
    (15, 'Therapeutics'):                         'Diagnostics & Health Access',
    (15, 'Biomaterials & Circular Economy'):      'Therapeutics',

    # CL16 Therapeutics — Cancer
    (16, 'Therapeutics'):                         'Diagnostics & Health Access',

    # CL17 Therapeutics — Regenerative
    (17, 'Therapeutics'):                         'Biomaterials & Circular Economy',
    (17, 'Diagnostics & Health Access'):          'Therapeutics',

    # CL18 Bioinputs — Pest / Biocontrol
    (18, 'Bioinputs & Crop Resilience'):          'Nature & Ecosystem Tech',

    # CL19 Food — Precision Fermentation
    (19, 'Food Systems & Alt Proteins'):          'Biomanufacturing & Fermentation Economy',
    (19, 'Biomanufacturing & Fermentation Economy'): 'Food Systems & Alt Proteins',
    (19, 'Biomaterials & Circular Economy'):      'Food Systems & Alt Proteins',
    (19, 'Diagnostics & Health Access'):          'Food Systems & Alt Proteins',

    # CL20 Bioinputs — Biologicals
    (20, 'Bioinputs & Crop Resilience'):          'Biomanufacturing & Fermentation Economy',
    (20, 'Biomanufacturing & Fermentation Economy'): 'Bioinputs & Crop Resilience',
    (20, 'Food Systems & Alt Proteins'):          'Biomaterials & Circular Economy',

    # CL21 Farm Intelligence — Agronomic
    (21, 'Farm Intelligence'):                    'Nature & Ecosystem Tech',
    (21, 'Nature & Ecosystem Tech'):              'Farm Intelligence',
    (21, 'Bioinputs & Crop Resilience'):          'Farm Intelligence',
    (21, 'Food Systems & Alt Proteins'):          'Farm Intelligence',
    (21, 'Biomanufacturing & Fermentation Economy'): 'Farm Intelligence',

    # CL22 Nature — Credit / Carbon
    (22, 'Nature & Ecosystem Tech'):              'Farm Intelligence',
    (22, 'Farm Intelligence'):                    'Nature & Ecosystem Tech',

    # CL23 Nature — Agri Food
    (23, 'Nature & Ecosystem Tech'):              'Farm Intelligence',
}

# ── Fetch candidates ──────────────────────────────────────────────────────────
cur.execute('''
SELECT sx.startup_id, e.canonical_name, sx.cluster_id, sx.bio_theme_primary
FROM startup_extended sx JOIN entities e ON e.entity_id=sx.startup_id
WHERE sx.cluster_id >= 0
  AND (sx.bio_theme_secondary IS NULL OR sx.bio_theme_secondary = '')
ORDER BY sx.cluster_id, e.canonical_name
''')
candidates = cur.fetchall()
print(f'Candidatos sin bio_theme_secondary: {len(candidates)}')
if args.dry_run:
    print('(modo dry-run - no se escribe nada)\n')
print()

updated = 0
skipped_no_data = 0
skipped_same = 0

for eid, name, cl_id, primary in candidates:
    # Try data-driven lookup first, then fallback
    secondary = DATA_LOOKUP.get((cl_id, primary)) or FALLBACK.get((cl_id, primary))

    if not secondary:
        print(f'  SKIP  CL{cl_id:<3} {name[:40]:<40}  primary={primary[:30]} (sin mapeo)')
        skipped_no_data += 1
        continue

    if secondary == primary:
        print(f'  SKIP  CL{cl_id:<3} {name[:40]:<40}  secondary=primary (omitido)')
        skipped_same += 1
        continue

    print(f'  OK    CL{cl_id:<3} {name[:40]:<40}  {primary[:28]:<28} -> {secondary}')

    if not args.dry_run:
        cur.execute(
            'UPDATE startup_extended SET bio_theme_secondary=? WHERE startup_id=?',
            (secondary, eid)
        )
        cur.execute(
            '''INSERT INTO audit_log
                 (timestamp, actor, entity_id, table_name, field, old_value, new_value, reason)
               VALUES (?,?,?,?,?,?,?,?)''',
            (now, 'auto:derive_secondary_themes', eid, 'startup_extended',
             'bio_theme_secondary', None, secondary,
             f'Derivado por patron de CL{cl_id}+primary o fallback de dominio')
        )
        updated += 1

if not args.dry_run:
    conn.commit()

conn.close()
print()
print(f'Actualizados     : {updated}')
print(f'Sin mapeo        : {skipped_no_data}')
print(f'Same-as-primary  : {skipped_same}')
