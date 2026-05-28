"""
fix_cl15_outliers.py
--------------------
Reasigna los 13 outliers del Cluster 15 (Diagnostics device/nanomedicine)
que HDBSCAN dejó con 35% de confianza a sus clusters correctos.

Diagnóstico:
  Cluster 15 (n=37, conf_avg=63%) tiene 13 outliers que semánticamente no son
  "diagnostics device/medtech/nanomedicine". El análisis de vocabulario muestra:
  - Biomanufacturing (ByBug, Stämm, Outpost, Plamic, Elytron) → CL5
  - Therapeutics Cancer (NanoproX, Galtec Life) → CL16
  - Therapeutics Biopharmaceutical (Amplify Dynamics, Lipock) → CL7
  - Diagnostics Lab (ArgenTAG, Gameet, Cellter) → CL0
  - Bioinputs Crop Protection (Botanical Solutions) → CL18

Ejecutar:
  .venv/Scripts/python.exe fix_cl15_outliers.py
"""

import sqlite3, pathlib, datetime, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
db = pathlib.Path('db/bio_latam.db')
conn = sqlite3.connect(db)
cur  = conn.cursor()
now  = datetime.datetime.now(datetime.UTC).isoformat()

# ── Label strings exactos de los clusters destino ─────────────────────────
LABELS = {
    0:  'Diagnostics & Health Access · Diagnostics||diagnostics · laboratory · diagnosis · portable',
    5:  'Biomanufacturing & Fermentation Economy · Precision Fermentation||bioindustrial · precision fermentation · enzymes · platforms',
    7:  'Therapeutics · Biopharmaceutical||biopharmaceutical · organ · therapeutic · medicine',
    16: 'Therapeutics · Cancer||cancer · therapeutics · metabolic · therapeutic',
    18: 'Bioinputs & Crop Resilience · Pest||pest · biocontrol · biologicals · crop',
}
BIO = {
    0:  'Diagnostics & Health Access',
    5:  'Biomanufacturing & Fermentation Economy',
    7:  'Therapeutics',
    16: 'Therapeutics',
    18: 'Bioinputs & Crop Resilience',
}

# ── Helpers ────────────────────────────────────────────────────────────────
def log(entity_id, field, old_val, new_val, reason):
    cur.execute(
        '''INSERT INTO audit_log
             (timestamp, actor, entity_id, table_name, field, old_value, new_value, reason)
           VALUES (?,?,?,?,?,?,?,?)''',
        (now, 'human:curador', entity_id, 'startup_extended', field,
         str(old_val) if old_val is not None else None,
         str(new_val), reason))

def move(slug, target_cl, reason):
    """Mueve un startup a un cluster distinto y corrige bio_theme_primary si es necesario."""
    cur.execute(
        '''SELECT e.entity_id, e.canonical_name,
                  sx.cluster_id, sx.bio_theme_primary
           FROM entities e
           JOIN startup_extended sx ON sx.startup_id = e.entity_id
           WHERE e.slug = ?''', (slug,))
    row = cur.fetchone()
    if not row:
        print(f'  NO ENCONTRADO: {slug}'); return

    eid, name, old_cl, old_bio = row
    new_bio = BIO[target_cl]
    new_label = LABELS[target_cl]

    # cluster_id + cluster_label
    cur.execute(
        'UPDATE startup_extended SET cluster_id=?, cluster_label=?, is_outlier=0 WHERE startup_id=?',
        (target_cl, new_label, eid))
    log(eid, 'cluster_id',    old_cl, target_cl,  reason)
    log(eid, 'cluster_label', None,   new_label,  reason)
    log(eid, 'is_outlier',    1,      0,           reason)

    # bio_theme_primary (solo si cambia)
    if old_bio != new_bio:
        cur.execute('UPDATE startup_extended SET bio_theme_primary=? WHERE startup_id=?',
                    (new_bio, eid))
        log(eid, 'bio_theme_primary', old_bio, new_bio, reason)
        bio_note = f'  bio: {old_bio} → {new_bio}'
    else:
        bio_note = ''

    print(f'  ✓ {name:<35} CL{old_cl} → CL{target_cl}{bio_note}')

# ── Reasignaciones ─────────────────────────────────────────────────────────

print('=== Cluster 15 outliers → Diagnostics Lab (CL0) ===')
# Estos son realmente Diagnostics pero del subtipo laboratorio/secuenciación
move('argentag-2',
     0, 'Single-cell sequencing kit → Diagnostics Lab (CL0), no device/nanomedicine (CL15)')
move('gameet-2',
     0, 'Microdevice for assisted reproduction → medtech/diagnostics lab (CL0)')
move('cellter',
     0, 'Sin descripción, bio_theme=Diagnostics → queda en Diagnostics Lab (CL0) por default')

print('\n=== Cluster 15 outliers → Biomanufacturing (CL5) ===')
move('bybug-2',
     5, 'Engineered insect bioreactors for recombinant proteins → Biomanufacturing (CL5)')
move('st-mm-2',
     5, 'High-throughput bioprocessing for biologics manufacturing → Biomanufacturing (CL5)')
move('outpost-2',
     5, 'Closed-loop microbiome predictive-biology platform → Biomanufacturing (CL5); bio_theme ya era Biomanufacturing')
move('plamic',
     5, 'Lab-on-a-chip for nanomedicine manufacturing → Biomanufacturing/process tech (CL5)')
move('elytron-biotech',
     5, 'AI-driven biological product development platform → Biomanufacturing (CL5); bio_theme era Biomaterials (incorrecto)')

print('\n=== Cluster 15 outliers → Therapeutics Cancer (CL16) ===')
move('nanoprox',
     16, 'Bismuth-sulfide radiosensitizer for oncology → Therapeutics Cancer (CL16)')
move('galtec-life',
     16, 'Galectin-modulating immunotherapies for cancer/inflammation → Therapeutics Cancer (CL16)')

print('\n=== Cluster 15 outliers → Therapeutics Biopharmaceutical (CL7) ===')
move('amplify-dynamics-2',
     7, 'Ultrasound purification for lipid nanoparticles → drug delivery platform → Biopharmaceutical (CL7)')
move('lipock',
     7, 'Lipid nanocapsule platform for hydrophobic actives → drug delivery → Biopharmaceutical (CL7)')

print('\n=== Cluster 15 outliers → Bioinputs Pest/Biocontrol (CL18) ===')
move('botanical-solutions-2',
     18, 'Botanical active ingredients from plant tissue culture → biopesticide/biocontrol → CL18')

# ── Commit ─────────────────────────────────────────────────────────────────
conn.commit()
conn.close()
print('\n✅ Commit OK — 13 outliers reasignados')
print('Próximo paso: python pipeline.py intelligence-data  (regenera el .js)')
