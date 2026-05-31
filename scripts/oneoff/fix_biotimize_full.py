"""
fix_biotimize_full.py
---------------------
Corrección editorial completa de Biotimize.

DIAGNÓSTICO:
  1. umap_x/umap_y = (+2.22, +2.60) → sentado encima de empresas de comida
     (Done Properly, SpecLab, HARMONY) en la región visual Food Systems.
     Causa: summary corto (2 frases) con palabras "yeast"/"bacteria"/"fermentation"
     → embedding débil, UMAP lo mandó al cluster de fermentación de alimentos.
     Biolinker (mismo CL19) está en (-8.69, -2.07) = región correcta de Biomanufacturing.

  2. cluster_label = "Food Systems & Alt Proteins — Precision Fermentation..."
     → el sidebar y el tooltip muestran "Food Systems" aunque bio_theme_primary
     = "Biomanufacturing & Platform Technologies" (ya corregido y locked).

  3. emergent_theme = "food systems & alt proteins — precision fermentation · dairy..."
     → campo derivado contaminado.

  4. startup_summary_en demasiado corta y genérica → embedding pobrisimo.
     data_quality_score = 0.0.

  5. technology_tags = "biomanufacturing; fermentation" — falta especificidad CDMO.

CORRECCIONES:
  A. Mover umap_x/umap_y a (-8.55, -1.95) — región Biomanufacturing, cerca de
     Biolinker (-8.69, -2.07). Corrección editorial justificada: UMAP 2D es
     distorsionador no-lineal; posición incorrecta produce lectura equivocada del mapa.

  B. Actualizar cluster_label a prefijo Biomanufacturing.

  C. Actualizar emergent_theme.

  D. Enriquecer startup_summary_en con terminología CDMO/biofarmacéutica específica.

  E. Actualizar technology_tags.

Fuente: BioProcess Insider (2022), PharmaSource profile, GlobeNewswire Series A.
Ejecutar:
  .venv/Scripts/python.exe fix_biotimize_full.py
"""

import sqlite3, pathlib, datetime, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

db   = pathlib.Path('db/bio_latam.db')
conn = sqlite3.connect(db)
cur  = conn.cursor()
now  = datetime.datetime.now(datetime.UTC).isoformat()
EID  = 'biotimize'

def log(field, old_val, new_val, reason):
    cur.execute(
        '''INSERT INTO audit_log
             (timestamp, actor, entity_id, table_name, field, old_value, new_value, reason)
           VALUES (?,?,?,?,?,?,?,?)''',
        (now, 'human:curador', EID, 'startup_extended', field,
         str(old_val) if old_val is not None else None,
         str(new_val), reason))

SOURCE = ('Diagnóstico editorial: CDMO biofarmacéutico (primer CDMO biológico en Brasil). '
          'Ref: BioProcess Insider 2022, PharmaSource profile. '
          'Posición UMAP corregida — 2D proyección no-lineal colocó la empresa en la región '
          'visual Food Systems por overlap semántico de "fermentation"/"yeast"/"bacteria" con '
          'empresas de alimentos. Biolinker (mismo CL19) está en (-8.69, -2.07) = región correcta.')

# ── 0. Leer valores actuales ──────────────────────────────────────────────────
cur_row = cur.execute('''
    SELECT sx.umap_x, sx.umap_y, sx.cluster_label, sx.emergent_theme,
           sx.startup_summary_en, sx.technology_tags
    FROM startup_extended sx JOIN entities e ON e.entity_id=sx.startup_id
    WHERE e.entity_id=?
''', (EID,)).fetchone()

if not cur_row:
    print(f'ERROR: {EID} not found in DB')
    sys.exit(1)

old_umap_x, old_umap_y, old_cl, old_et, old_sum, old_tech = cur_row

print(f'=== Valores actuales ===')
print(f'  umap: ({old_umap_x:.3f}, {old_umap_y:.3f})')
print(f'  cluster_label: {old_cl}')
print(f'  emergent_theme: {old_et}')
print(f'  technology_tags: {old_tech}')
print(f'  summary (primeras 100): {str(old_sum)[:100]}')

# ── A. Mover UMAP ─────────────────────────────────────────────────────────────
NEW_X = -8.55
NEW_Y = -1.95
cur.execute('UPDATE startup_extended SET umap_x=?, umap_y=? WHERE startup_id=?',
            (NEW_X, NEW_Y, EID))
log('umap_x', old_umap_x, NEW_X, SOURCE)
log('umap_y', old_umap_y, NEW_Y, SOURCE)
print(f'\nA. UMAP: ({old_umap_x:.2f}, {old_umap_y:.2f}) → ({NEW_X}, {NEW_Y})')

# ── B. cluster_label ──────────────────────────────────────────────────────────
NEW_CL = ('Biomanufacturing & Platform Technologies — CDMOs & Bioprocess Development'
          '||cdmo · biopharmaceutical · contract manufacturing · biosimilars · mammalian-cells')
cur.execute('UPDATE startup_extended SET cluster_label=? WHERE startup_id=?', (NEW_CL, EID))
log('cluster_label', old_cl, NEW_CL, SOURCE)
print(f'B. cluster_label → {NEW_CL[:70]}…')

# ── C. emergent_theme ─────────────────────────────────────────────────────────
NEW_ET = ('biomanufacturing & platform technologies — cdmo · biopharmaceutical '
          '· contract manufacturing · biosimilars · monoclonal antibodies')
cur.execute('UPDATE startup_extended SET emergent_theme=? WHERE startup_id=?', (NEW_ET, EID))
log('emergent_theme', old_et, NEW_ET, SOURCE)
print(f'C. emergent_theme → {NEW_ET[:80]}…')

# ── D. Enriquecer startup_summary_en ──────────────────────────────────────────
NEW_SUM = (
    'Brazilian biopharmaceutical CDMO (Contract Development and Manufacturing Organization) '
    'and the first biological CDMO in operation in Brazil. Provides end-to-end bioprocess '
    'development and GMP-grade manufacturing services for recombinant proteins, monoclonal '
    'antibodies, and biosimilars using mammalian cell culture (CHO, HEK), yeast, and '
    'bacterial expression systems. Supports global biotech and pharma companies, research '
    'institutions, and the public sector in scaling clinical and commercial biologics '
    'production in Latin America. Raised a USD 30M Series A to build the first full-scale '
    'biological GMP production facility (20,000 m²) in Brazil, reducing dependence on '
    'imported biopharmaceuticals.'
)
cur.execute('UPDATE startup_extended SET startup_summary_en=?, startup_summary_v1=? WHERE startup_id=?',
            (NEW_SUM, NEW_SUM, EID))
log('startup_summary_en', old_sum, NEW_SUM, SOURCE)
print(f'D. startup_summary_en enriched ({len(NEW_SUM)} chars vs {len(str(old_sum))} chars)')

# ── E. technology_tags ────────────────────────────────────────────────────────
NEW_TECH = 'biomanufacturing; cdmo; bioreactor; monoclonal-antibodies; biosimilars; recombinant-proteins; gmp; mammalian-cell-culture'
cur.execute('UPDATE startup_extended SET technology_tags=? WHERE startup_id=?', (NEW_TECH, EID))
log('technology_tags', old_tech, NEW_TECH, SOURCE)
print(f'E. technology_tags → {NEW_TECH}')

conn.commit()
conn.close()
print('\nCommit OK — regenerar startup-themes-data.js con: python pipeline.py intelligence-data')
