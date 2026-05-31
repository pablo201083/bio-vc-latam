"""
apply_tech_depth_overrides.py
------------------------------
Lee quality/tech_depth_review.csv, aplica las correcciones manuales
en la columna "tech_depth_override" a startup_extended.

Uso:
  1. Abrir quality/tech_depth_review.csv en Excel
  2. Completar "tech_depth_override" (deep / applied / enabler) donde el
     clasificador automático esté equivocado. Dejar vacío si está bien.
  3. Guardar como CSV (UTF-8)
  4. Ejecutar:  .venv/Scripts/python.exe apply_tech_depth_overrides.py
"""

import sqlite3, pathlib, datetime, sys, csv
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

REVIEW_CSV = pathlib.Path('quality/tech_depth_review.csv')
DB = pathlib.Path('db/bio_latam.db')
VALID = {'deep', 'applied', 'enabler'}

if not REVIEW_CSV.exists():
    print(f'ERROR: {REVIEW_CSV} no encontrado.')
    sys.exit(1)

conn = sqlite3.connect(DB)
cur  = conn.cursor()
now  = datetime.datetime.now(datetime.UTC).isoformat()

overrides = []
with open(REVIEW_CSV, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        override = (row.get('tech_depth_override') or '').strip().lower()
        if override in VALID:
            overrides.append({
                'entity_id': row['entity_id'].strip(),
                'override':  override,
                'auto':      row['tech_depth_auto'].strip(),
                'notes':     row.get('notes', '').strip(),
            })

if not overrides:
    print('No hay overrides en el CSV. Nada que aplicar.')
    sys.exit(0)

print(f'Aplicando {len(overrides)} overrides...\n')
applied = 0
for o in overrides:
    cur.execute(
        'UPDATE startup_extended SET tech_depth=?, tech_depth_confidence=1.0, tech_depth_basis=? WHERE startup_id=?',
        (o['override'],
         f'human:override — curador cambió {o["auto"]} → {o["override"]}. Notas: {o["notes"] or "—"}',
         o['entity_id']))
    cur.execute(
        '''INSERT INTO audit_log (timestamp, actor, entity_id, table_name, field, old_value, new_value, reason)
           VALUES (?,?,?,?,?,?,?,?)''',
        (now, 'human:curador', o['entity_id'], 'startup_extended', 'tech_depth',
         o['auto'], o['override'],
         f'override manual en tech_depth_review.csv. Notas: {o["notes"] or "—"}'))
    print(f'  ✓  {o["entity_id"]}: {o["auto"]} → {o["override"]}  |  {o["notes"][:60]}')
    applied += 1

conn.commit()
conn.close()
print(f'\n{applied} overrides aplicados. Commit OK.')
print('\nPosteriormente regenerar el dashboard:')
print('  .venv/Scripts/python.exe -c "import sqlite3,sys;sys.path.insert(0,\'.\');from src.clustering import write_dashboard_data;conn=sqlite3.connect(\'db/bio_latam.db\');write_dashboard_data(conn);conn.close()"')
