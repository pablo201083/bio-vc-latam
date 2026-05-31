"""
fix_cluster_label_mismatches.py
---------------------------------
Corrige los 19 casos donde bio_theme_primary ≠ prefijo de cluster_label.

Causa raíz: el pipeline asigna cluster_label basado en el cluster HDBSCAN
dominante, que no siempre coincide con el bio_theme_primary asignado por
el curador. Los labels de sidebar y tooltips mostraban el tema equivocado.

Estrategia:
  - Reemplazar el prefijo de cluster_label con bio_theme_primary
  - Asignar keywords descriptivas de lo que la empresa realmente hace
  - Todos los cambios se registran como human:curador en audit_log

Grupos de casos:
  CL0  — Gen-t, Pharmalens (Therapeutics en cluster Diagnostics)
  CL1  — Aquit, WerkénVac (Bioinputs en cluster Fish/Food)
  CL2  — HIF Global, Sistema.bio (Nature en cluster Biomaterials)
  CL4  — CIRCCLO, MUTA (Biomaterials en cluster Nature)
  CL7  — Cellargen Biotech, Neocell (Biomanufacturing en cluster Therapeutics)
  CL10 — nChemi (Therapeutics en cluster Biomaterials)
  CL15 — Merken Biotech (Therapeutics en cluster Diagnostics)
  CL19 — AGES, Biolinker, Imeve, Inprenha, Qnity (5 temas en cluster Food/Fermentation)
  CL20 — Algalife (Biomanufacturing en cluster Bioinputs)
  CL21 — AGROTOOLS (Nature en cluster Farm Intelligence)

Ejecutar:
  .venv/Scripts/python.exe fix_cluster_label_mismatches.py
"""

import sqlite3, pathlib, datetime, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

db   = pathlib.Path('db/bio_latam.db')
conn = sqlite3.connect(db)
cur  = conn.cursor()
now  = datetime.datetime.now(datetime.UTC).isoformat()

def log(eid, field, old_val, new_val, reason):
    cur.execute(
        '''INSERT INTO audit_log
             (timestamp, actor, entity_id, table_name, field, old_value, new_value, reason)
           VALUES (?,?,?,?,?,?,?,?)''',
        (now, 'human:curador', eid, 'startup_extended', field,
         str(old_val) if old_val is not None else None,
         str(new_val), reason))

REASON = ('cluster_label prefix ≠ bio_theme_primary: prefijo actualizado para que '
          'sidebar y tooltips reflejen el tema correcto. Keywords asignadas según '
          'actividad real de la empresa, no según cluster HDBSCAN dominante.')

# ─────────────────────────────────────────────────────────────────────────────
# Mapa: entity_id → nuevo cluster_label
# Formato: "Prefijo — Sub-label||keyword1 · keyword2 · ..."
# ─────────────────────────────────────────────────────────────────────────────
CORRECTIONS = {

    # CL0 — Therapeutics en cluster Diagnostics
    # Gen-t: genomics de diversidad étnica → Genomics & Precision Medicine
    'gen-t': (
        'Therapeutics — Genomics & Precision Medicine'
        '||genomics · ethnic diversity · precision medicine · genome sequencing'
    ),
    # Pharmalens: computer vision para QC en manufactura farmacéutica → Digital Health & Medtech
    'pharmalens': (
        'Therapeutics — Digital Health & Medtech'
        '||computer vision · quality control · pharmaceutical manufacturing · automation · ai'
    ),

    # CL1 — Bioinputs en cluster Fish/Food
    # Aquit: tratamientos preventivos de inmunidad en peces → Aquaculture Biologicals
    'aquit': (
        'Bioinputs & Crop Resilience — Aquaculture Biologicals'
        '||aquaculture · fish immunity · bioprotection · animal health · preventive treatments'
    ),
    # WerkénVac: vacuna de RNA auto-amplificante para peces → Aquaculture Biologicals
    'werkenvac': (
        'Bioinputs & Crop Resilience — Aquaculture Biologicals'
        '||aquaculture · rna vaccine · fish health · animal health · biosecurity'
    ),

    # CL2 — Nature en cluster Biomaterials
    # HIF Global: e-fuels desde hidrógeno verde + CO2 capturado → Nature-Based Solutions
    'hif-global': (
        'Nature & Ecosystem Tech — Nature-Based Solutions'
        '||e-fuels · green hydrogen · carbon capture · electrolysis · decarbonization'
    ),
    # Sistema.bio: biodigestores modulares para agricultores → Restoration & Nature Finance
    'sistema-bio': (
        'Nature & Ecosystem Tech — Restoration & Nature Finance'
        '||biodigester · biogas · organic waste · smallholder · circular agriculture'
    ),

    # CL4 — Biomaterials en cluster Nature-Based Solutions
    # CIRCCLO: packaging reutilizable economía circular → Circular Economy & Packaging
    'circclo': (
        'Biomaterials & Circular Economy — Circular Economy & Packaging'
        '||circular economy · reusable packaging · cpg · waste reduction · brand'
    ),
    # MUTA: marketplace de reciclaje → Circular Economy & Packaging
    'muta': (
        'Biomaterials & Circular Economy — Circular Economy & Packaging'
        '||circular economy · recycling · waste · materials recovery · marketplace'
    ),

    # CL7 — Biomanufacturing en cluster Therapeutics
    # Cellargen Biotech: CRO que desarrolla vacunas recombinantes, hormonas → CDMOs
    'cellargen-biotech': (
        'Biomanufacturing & Platform Technologies — CDMOs & Bioprocess Development'
        '||cdmo · recombinant · biopharmaceutical · vaccines · hormones · contract'
    ),
    # Neocell: desarrollo y manufactura de biosimilares y biológicos → CDMOs
    'neocell': (
        'Biomanufacturing & Platform Technologies — CDMOs & Bioprocess Development'
        '||cdmo · biosimilars · biologics · biomanufacturing · process development'
    ),

    # CL10 — Therapeutics en cluster Biomaterials
    # nChemi: recubrimientos nanopartícula antimicrobiana para instrumental quirúrgico
    'nchemi': (
        'Therapeutics — Medtech & Devices'
        '||nanotechnology · antimicrobial coating · surgical instruments · medical device · nanomaterials'
    ),

    # CL15 — Therapeutics en cluster Diagnostics
    # Merken Biotech: CRO full-stack de R&D (biología molecular, farmacoquinética)
    'merken-biotech': (
        'Therapeutics — CROs & Drug Development Services'
        '||cro · molecular biology · pharmacokinetics · drug development · cell assays'
    ),

    # CL19 — 5 temas mezclados en cluster Food/Fermentation (cluster metodológico)
    # AGES: moléculas bioactivas del Amazonas para healthspan → Bioactives & Functional Ingredients
    'ages': (
        'Biomaterials & Circular Economy — Bioactives & Natural Chemistry'
        '||amazon · bioactive molecules · healthspan · longevity · natural extracts'
    ),
    # Biolinker: plataforma de ingeniería de proteínas / bio sintética → CDMOs & Bioprocess
    'biolinker-synthetic-biology': (
        'Biomanufacturing & Platform Technologies — CDMOs & Bioprocess Development'
        '||synthetic biology · protein engineering · gene synthesis · mrna · cell-free expression'
    ),
    # Imeve: aditivos probióticos y medicamentos para salud animal → Animal Health
    'imeve': (
        'Bioinputs & Crop Resilience — Animal Health & Bioinputs'
        '||probiotics · animal health · additives · supplements · veterinary · livestock'
    ),
    # Inprenha: biotecnología de reproducción animal → Animal Health
    'inprenha': (
        'Bioinputs & Crop Resilience — Animal Health & Bioinputs'
        '||animal reproduction · protein technology · cattle · pregnancy rates · reproductive biotech'
    ),
    # Qnity: chip quantum-electroquímico para drug discovery → Molecular Diagnostics
    'qnity': (
        'Diagnostics & Health Access — Molecular Diagnostics'
        '||quantum electrochemical · drug discovery · affinity screening · molecular sensing · chip'
    ),

    # CL20 — Biomanufacturing en cluster Bioinputs
    # Algalife: plataforma de optimización de procesos con microalgas
    'algalife': (
        'Biomanufacturing & Platform Technologies — Algae & Bioprocess Platforms'
        '||microalgae · platform · bioprocess optimization · production · biomass'
    ),

    # CL21 — Nature en cluster Farm Intelligence
    # AGROTOOLS: plataforma de inteligencia agropecuaria → Traceability & Transparency
    'agrotools': (
        'Nature & Ecosystem Tech — Traceability & Transparency'
        '||agribusiness intelligence · land · supply chain · corporate sustainability · compliance'
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
print(f'=== fix_cluster_label_mismatches.py — {len(CORRECTIONS)} correcciones ===\n')

fixed = 0
for eid, new_label in CORRECTIONS.items():
    # resolve entity_id (puede tener variaciones)
    row = cur.execute('''
        SELECT e.entity_id, e.canonical_name, sx.cluster_label, sx.bio_theme_primary
        FROM startup_extended sx JOIN entities e ON e.entity_id=sx.startup_id
        WHERE e.entity_id=?
    ''', (eid,)).fetchone()

    if not row:
        # try partial match on canonical_name
        safe = eid.replace('-', ' ')
        row = cur.execute('''
            SELECT e.entity_id, e.canonical_name, sx.cluster_label, sx.bio_theme_primary
            FROM startup_extended sx JOIN entities e ON e.entity_id=sx.startup_id
            WHERE lower(replace(e.entity_id,'-',' ')) LIKE ?
               OR lower(e.canonical_name) LIKE ?
        ''', (f'%{safe}%', f'%{safe}%')).fetchone()

    if not row:
        print(f'  NOT FOUND: {eid}')
        continue

    real_eid, name, old_label, bio_theme = row
    cur.execute('UPDATE startup_extended SET cluster_label=? WHERE startup_id=?',
                (new_label, real_eid))
    log(real_eid, 'cluster_label', old_label, new_label, REASON)

    old_prefix = (old_label or '').split(' — ')[0]
    new_prefix = new_label.split(' — ')[0]
    print(f'  ✓  {name:<38}  {old_prefix[:35]:<35} → {new_prefix}')
    fixed += 1

conn.commit()
conn.close()
print(f'\n{fixed}/{len(CORRECTIONS)} labels corregidos. Commit OK.')
print('\nProximo paso: regenerar dashboard')
print('  .venv/Scripts/python.exe -c "import sqlite3,sys;sys.path.insert(0,\'.\');'
      'from src.clustering import write_dashboard_data;conn=sqlite3.connect(\'db/bio_latam.db\');'
      'write_dashboard_data(conn);conn.close()"')
