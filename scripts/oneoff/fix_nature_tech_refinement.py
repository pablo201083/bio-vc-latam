"""
fix_nature_tech_refinement.py
------------------------------
Refinamiento de Nature & Ecosystem Tech a partir del análisis de sub-clusters
vs. framework Nature Tech (Antom, 2025) — 4 funciones: Deploy, MRV, Transparencia, Conexión.

Cambios:
  1. CL22 "Credit" → Farm Intelligence (13 agrifintech de crédito agrícola mal asignados)
     - bio_theme_primary: Nature → Farm Intelligence
     - cluster_label: nuevo prefijo "Farm Intelligence — Agrifintech & Rural Credit"

  2. Renombrar sub-labels de clusters Nature Tech restantes con framework Antom:
     - CL4  → "Nature & Ecosystem Tech — Nature-Based Solutions"
     - CL13 → "Nature & Ecosystem Tech — MRV & Biodiversity Intelligence"
     - CL14 → "Nature & Ecosystem Tech — Restoration & Nature Finance"
     - CL23 → "Nature & Ecosystem Tech — Traceability & Transparency"

  NOTA CL4: Contiene 3 startups de cleantech genérica (Splight, Branch Energy, Solfium)
  que no encajan estrictamente en Nature Tech. Se mantienen aquí (sin theme mejor disponible)
  pero se documenta la divergencia. Candidatas a revisión si se crea un tema Cleantech.

  SKIPS: entradas con actor='human:curador' en audit_log (locked).

Ejecutar:
  .venv/Scripts/python.exe fix_nature_tech_refinement.py
"""

import sqlite3, pathlib, datetime, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

db   = pathlib.Path('db/bio_latam.db')
conn = sqlite3.connect(db)
cur  = conn.cursor()
now  = datetime.datetime.now(datetime.UTC).isoformat()

# ── Helpers ──────────────────────────────────────────────────────────────────

def locked_ids(conn):
    return {r[0] for r in conn.execute(
        "SELECT DISTINCT entity_id FROM audit_log "
        "WHERE field='bio_theme_primary' AND actor='human:curador'"
    )}

def log(entity_id, field, old_val, new_val, reason):
    cur.execute(
        '''INSERT INTO audit_log
             (timestamp, actor, entity_id, table_name, field, old_value, new_value, reason)
           VALUES (?,?,?,?,?,?,?,?)''',
        (now, 'human:curador', entity_id, 'startup_extended', field,
         str(old_val) if old_val is not None else None,
         str(new_val), reason))

LOCKED = locked_ids(conn)

# ─────────────────────────────────────────────────────────────────────────────
# CAMBIO 1: CL22 → Farm Intelligence
# ─────────────────────────────────────────────────────────────────────────────
print('=== CAMBIO 1: CL22 (Agrifintech) → Farm Intelligence ===')

OLD_BIO = 'Nature & Ecosystem Tech'
NEW_BIO = 'Farm Intelligence'
OLD_LABEL_PREFIX = 'Nature & Ecosystem Tech — Credit'
NEW_LABEL = 'Farm Intelligence — Agrifintech & Rural Credit||agrifintech · credit · financing · rural · risk'

rows_cl22 = cur.execute('''
    SELECT e.entity_id, e.canonical_name, sx.bio_theme_primary, sx.cluster_label
    FROM startup_extended sx JOIN entities e ON e.entity_id=sx.startup_id
    WHERE sx.cluster_id=22 AND sx.scope_decision='include'
''').fetchall()

moved = 0
skipped = 0
for eid, name, old_bio, old_label in rows_cl22:
    if eid in LOCKED:
        print(f'  SKIP (locked)  {name}')
        skipped += 1
        continue

    # Update bio_theme_primary
    if old_bio != NEW_BIO:
        cur.execute('UPDATE startup_extended SET bio_theme_primary=? WHERE startup_id=?',
                    (NEW_BIO, eid))
        log(eid, 'bio_theme_primary', old_bio, NEW_BIO,
            'CL22 agrifintech mal asignado a Nature Tech — plataformas de crédito agrícola '
            'pertenecen a Farm Intelligence. Ref: análisis vs framework Nature Tech (Antom 2025)')

    # Update cluster_label
    if old_label and old_label.startswith(OLD_LABEL_PREFIX):
        cur.execute('UPDATE startup_extended SET cluster_label=? WHERE startup_id=?',
                    (NEW_LABEL, eid))
        log(eid, 'cluster_label', old_label, NEW_LABEL,
            'CL22 reasignado a Farm Intelligence — sub-label actualizado')

    print(f'  OK  {name:<45}  {old_bio} → {NEW_BIO}')
    moved += 1

print(f'  Total: {moved} movidas, {skipped} skipped (locked)')

# ─────────────────────────────────────────────────────────────────────────────
# CAMBIO 2: Renombrar sub-labels de clusters Nature Tech con framework Antom
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== CAMBIO 2: Sub-labels Nature Tech → framework Antom (4 funciones) ===')

RENAMES = [
    # (cluster_id, old_prefix, new_label, nota)
    (4,  'Nature & Ecosystem Tech — Energy',
          'Nature & Ecosystem Tech — Nature-Based Solutions||ocean · biochar · regenerative · marine · bioenergy',
          'Función Despliegue: restauración/remoción de carbono basada en naturaleza'),
    (13, 'Nature & Ecosystem Tech — Satellite',
          'Nature & Ecosystem Tech — MRV & Biodiversity Intelligence||satellite · monitoring · biodiversity · remote sensing',
          'Función MRV: monitoreo y verificación de ecosistemas via sensores/satélites'),
    (14, 'Nature & Ecosystem Tech — Nature Finance',
          'Nature & Ecosystem Tech — Restoration & Nature Finance||restoration · reforestation · carbon · conservation · NbS',
          'Función Despliegue + Conexión: restauración forestal a escala y mercados de carbono/biodiversidad'),
    (23, 'Nature & Ecosystem Tech — Agri Food',
          'Nature & Ecosystem Tech — Traceability & Transparency||traceability · supply chain · compliance · sustainability · water',
          'Función Transparencia: trazabilidad y cumplimiento de cadenas agroalimentarias'),
]

for cl_id, old_prefix, new_label, nota in RENAMES:
    rows = cur.execute('''
        SELECT e.entity_id, e.canonical_name, sx.cluster_label
        FROM startup_extended sx JOIN entities e ON e.entity_id=sx.startup_id
        WHERE sx.cluster_id=? AND sx.scope_decision='include'
          AND sx.cluster_label LIKE ?
    ''', (cl_id, old_prefix + '%')).fetchall()

    count = 0
    for eid, name, old_label in rows:
        cur.execute('UPDATE startup_extended SET cluster_label=? WHERE startup_id=?',
                    (new_label, eid))
        log(eid, 'cluster_label', old_label, new_label, nota)
        count += 1
    print(f'  CL{cl_id:>2}  {count:>2} labels → [{new_label.split("||")[0]}]')

# ─────────────────────────────────────────────────────────────────────────────
# NOTA: CL4 cleantech outliers (no se mueven — documentados)
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== NOTA: CL4 cleantech-only startups (no reasignadas — pendiente) ===')
cleantech_ids = ['splight', 'branch-energy', 'solfium-mx']
for eid in cleantech_ids:
    row = cur.execute(
        "SELECT e.canonical_name, sx.bio_theme_primary FROM startup_extended sx "
        "JOIN entities e ON e.entity_id=sx.startup_id WHERE e.entity_id=?", (eid,)
    ).fetchone()
    if row:
        print(f'  PENDIENTE  {row[0]} — [{row[1]}] — cleantech genérica, sin tema BIO mejor disponible')
    else:
        # Try partial match
        row2 = cur.execute(
            "SELECT e.entity_id, e.canonical_name, sx.bio_theme_primary FROM startup_extended sx "
            "JOIN entities e ON e.entity_id=sx.startup_id "
            "WHERE e.canonical_name LIKE ? OR e.entity_id LIKE ?",
            (f'%{eid.split("-")[0].title()}%', f'%{eid}%')
        ).fetchone()
        if row2:
            print(f'  PENDIENTE  {row2[1]} (id={row2[0]}) — cleantech genérica')
        else:
            print(f'  (no encontrado en DB: {eid})')

conn.commit()
conn.close()
print('\nCommit OK')
print('\nProximo paso: regenerar dashboard')
print('  .venv/Scripts/python.exe -c "import sqlite3,sys; sys.path.insert(0,\'.\'); '
      'from src.clustering import write_dashboard_data; conn=sqlite3.connect(\'db/bio_latam.db\'); '
      'write_dashboard_data(conn); conn.close()"')
