"""
fix_round7_outliers.py
-----------------------
Round 7 of manual cluster corrections.

Moves:
  CL16 → CL7:  naiad-drug-design-br  (GPCR small-molecule discovery ≠ cancer)
  CL16 → CL7:  nintx-br              (plant-derived drugs for Alzheimer's ≠ cancer)
  CL11 → CL18: arakion               (arachnid-venom insecticide = pest biocontrol)
  CL11 → CL18: syocin-biotech        (biobactericide for crops = pest biocontrol)
  CL7  → CL11: sciphage              (phage products for poultry/aquaculture = biologicals)
  CL3  → CL6:  nutrition-from-water-cl (microalgae-based protein food = food novel ingredients)

Ejecutar:
  .venv/Scripts/python.exe fix_round7_outliers.py
"""

import sqlite3, pathlib, datetime, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

db = pathlib.Path('db/bio_latam.db')
conn = sqlite3.connect(db)
cur  = conn.cursor()
now  = datetime.datetime.now(datetime.UTC).isoformat()

LABELS = {
    6:  'Food Systems & Alt Proteins — Novel Ingredients||novel ingredients · functional · nutraceutical · fermentation',
    7:  'Therapeutics — Biopharmaceutical||biopharmaceutical · organ · therapeutic · medicine',
    11: 'Bioinputs & Crop Resilience — Biologicals Crop||biologicals · soil · microbial · plant',
    18: 'Bioinputs & Crop Resilience — Pest||pest · biocontrol · biologicals · crop',
}
BIO = {
    6:  'Food Systems & Alt Proteins',
    7:  'Therapeutics',
    11: 'Bioinputs & Crop Resilience',
    18: 'Bioinputs & Crop Resilience',
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

    print(f'  OK  {name:<40} CL{old_cl} -> CL{target_cl}{bio_note}')

# ── Reasignaciones ─────────────────────────────────────────────────────────

print('=== CL16 (Cancer) outliers -> CL7 (Biopharmaceutical) ===')
move('naiad-drug-design-br',
     7, 'GPCR modulator small-molecule discovery (STYX platform) - not cancer-specific, general biopharmaceutical drug discovery')
move('nintx-br',
     7, 'Plant-derived drug discovery (GAIApath) for Alzheimer\'s and metabolic diseases - not cancer; biopharmaceutical drug discovery')

print('\n=== CL11 (Biologicals Crop) outliers -> CL18 (Pest/Biocontrol) ===')
move('arakion',
     18, 'Arachnid-venom bioinsecticides to protect crops - pest biocontrol, not general biologicals')
move('syocin-biotech',
     18, 'High-precision protein biobactericides for crop protection against bacterial phytopathogens - pest biocontrol')

print('\n=== CL7 (Biopharmaceutical) -> CL11 (Biologicals) ===')
move('sciphage',
     11, 'Bacteriophage bioproducts (SalmoFree) for poultry/aquaculture pathogen control - biologicals for animal/food production, not biopharmaceutical')

print('\n=== CL3 (Packaging) -> CL6 (Food Novel Ingredients) ===')
move('nutrition-from-water-cl',
     6, 'Microalgae-based protein as drinkable food/sustainable protein - alt protein food product, not packaging material')

conn.commit()
conn.close()
print('\nCommit OK -- 6 reasignaciones round 7')
