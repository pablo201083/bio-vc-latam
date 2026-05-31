"""
fix_cl17_outliers.py
--------------------
Reasigna 6 outliers del Cluster 17 (Therapeutics Regenerative) que semanticamente
no son "regenerative medicine / cell therapy / tissue engineering".

Diagnostico:
  CL17 tiene 8 outliers con confianza 0.34-0.37. Los analizamos y 6 son incorrectos:

  - aplife_biotech      → CL0  (aptamer synthesis platform = Diagnostics/LifeSci Tools)
  - dogma_biotech       → CL7  (glycan-enhanced biologics = Biopharmaceutical)
  - tesabio_ai          → CL7  (small molecule drug discovery = Biopharmaceutical)
  - autem-therapeutics-br → CL16 (electromagnetic device for solid tumors = Cancer)
  - cellco              → CL7  (synthetic biology therapeutics platform = Biopharmaceutical)
  - nanotransfer        → CL7  (non-viral gene delivery nanoparticles = Biopharmaceutical)

  Los 2 que quedan en CL17 (Amnova Biotech, InSitu) SON regenerative medicine:
    Amnova: injectable bioactive hydrogel from human birth tissue
    InSitu: 3D biobandage with stem cells for wound healing

Ejecutar:
  .venv/Scripts/python.exe fix_cl17_outliers.py
"""

import sqlite3, pathlib, datetime, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

db = pathlib.Path('db/bio_latam.db')
conn = sqlite3.connect(db)
cur  = conn.cursor()
now  = datetime.datetime.now(datetime.UTC).isoformat()

LABELS = {
    0:  'Diagnostics & Health Access — Diagnostics||diagnostics · laboratory · diagnosis · portable',
    7:  'Therapeutics — Biopharmaceutical||biopharmaceutical · organ · therapeutic · medicine',
    16: 'Therapeutics — Cancer||cancer · therapeutics · metabolic · therapeutic',
}
BIO = {
    0:  'Diagnostics & Health Access',
    7:  'Therapeutics',
    16: 'Therapeutics',
}

def log(entity_id, field, old_val, new_val, reason):
    cur.execute(
        '''INSERT INTO audit_log
             (timestamp, actor, entity_id, table_name, field, old_value, new_value, reason)
           VALUES (?,?,?,?,?,?,?,?)''',
        (now, 'human:curador', entity_id, 'startup_extended', field,
         str(old_val) if old_val is not None else None,
         str(new_val), reason))

def move(entity_id, target_cl, reason):
    cur.execute(
        '''SELECT e.entity_id, e.canonical_name, sx.cluster_id, sx.bio_theme_primary
           FROM entities e JOIN startup_extended sx ON sx.startup_id=e.entity_id
           WHERE e.entity_id=?''', (entity_id,))
    row = cur.fetchone()
    if not row:
        print(f'  NO ENCONTRADO: {entity_id}'); return

    eid, name, old_cl, old_bio = row
    new_bio   = BIO[target_cl]
    new_label = LABELS[target_cl]

    cur.execute(
        'UPDATE startup_extended SET cluster_id=?, cluster_label=?, is_outlier=0 WHERE startup_id=?',
        (target_cl, new_label, eid))
    log(eid, 'cluster_id',    old_cl, target_cl,  reason)
    log(eid, 'cluster_label', None,   new_label,  reason)
    log(eid, 'is_outlier',    1,      0,           reason)

    if old_bio != new_bio:
        cur.execute('UPDATE startup_extended SET bio_theme_primary=? WHERE startup_id=?',
                    (new_bio, eid))
        log(eid, 'bio_theme_primary', old_bio, new_bio, reason)
        bio_note = f'  bio: {old_bio} -> {new_bio}'
    else:
        bio_note = ''

    print(f'  OK  {name:<40} CL17 -> CL{target_cl}{bio_note}')

# ── Reasignaciones ─────────────────────────────────────────────────────────

print('=== CL17 outliers -> Diagnostics (CL0) ===')
move('aplife_biotech',
     0, 'Aptamer synthesis platform for drug discovery / diagnostics / biosensors -> Diagnostics LifeSci Tools (CL0)')

print('\n=== CL17 outliers -> Biopharmaceutical (CL7) ===')
move('dogma_biotech',
     7, 'AI-discovered glycans to enhance biologics efficacy -> drug enhancement platform -> Biopharmaceutical (CL7)')
move('tesabio_ai',
     7, 'Small-molecule reprogram miRNA networks -> drug discovery -> Biopharmaceutical (CL7)')
move('cellco',
     7, 'Synthetic biology + AI to design next-generation medicines -> Biopharmaceutical (CL7)')
move('nanotransfer',
     7, 'Non-viral gene delivery via metal-oxide nanoparticles -> drug delivery -> Biopharmaceutical (CL7)')

print('\n=== CL17 outliers -> Cancer (CL16) ===')
move('autem-therapeutics-br',
     16, 'AutEMsys electromagnetic device for solid tumors (HCC) -> Therapeutics Cancer (CL16)')

conn.commit()
conn.close()
print('\nCommit OK -- 6 outliers reasignados desde CL17')
print('Amnova Biotech y InSitu se quedan en CL17 (son genuinamente regenerative medicine)')
