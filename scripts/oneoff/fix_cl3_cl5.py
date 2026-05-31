import sqlite3, pathlib, sys, datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
db = pathlib.Path('db/bio_latam.db')
conn = sqlite3.connect(db)
cur = conn.cursor()
now = datetime.datetime.now(datetime.UTC).isoformat()

LABELS = {
    3: 'Ag Biologicals & Bioinputs||biologicals · bioinputs · crop resilience · microbial',
    4: 'Farm Intelligence & Precision Agriculture||precision agriculture · agtech · satellite · AI',
    5: 'Food Systems & Alt Proteins||food biotech · alt proteins · novel ingredients · functional',
    6: 'Biomanufacturing & Precision Fermentation||fermentation · synthetic biology · biomanufacturing · platform',
}

def log(entity_id, field, old_val, new_val, reason):
    cur.execute(
        '''INSERT INTO audit_log (timestamp, actor, entity_id, table_name, field, old_value, new_value, reason)
           VALUES (?,?,?,?,?,?,?,?)''',
        (now, 'human:curador', entity_id, 'startup_extended', field,
         str(old_val) if old_val else None, str(new_val), reason))

def fix_bio(startup_id, new_bio, reason):
    cur.execute('SELECT bio_theme_primary, canonical_name FROM startup_extended sx '
                'JOIN entities e ON e.entity_id=sx.startup_id WHERE sx.startup_id=?', (startup_id,))
    row = cur.fetchone()
    if not row:
        print(f'  NOT FOUND: {startup_id}'); return
    old_bio, name = row
    if old_bio == new_bio:
        print(f'  SKIP {name}: already correct'); return
    cur.execute('UPDATE startup_extended SET bio_theme_primary=? WHERE startup_id=?', (new_bio, startup_id))
    log(startup_id, 'bio_theme_primary', old_bio, new_bio, reason)
    print(f'  bio OK  {name}: {old_bio} -> {new_bio}')

def move_cluster(startup_id, new_cl, new_bio, reason):
    cur.execute('SELECT cluster_id, bio_theme_primary, canonical_name FROM startup_extended sx '
                'JOIN entities e ON e.entity_id=sx.startup_id WHERE sx.startup_id=?', (startup_id,))
    row = cur.fetchone()
    if not row:
        print(f'  NOT FOUND: {startup_id}'); return
    old_cl, old_bio, name = row
    cur.execute('UPDATE startup_extended SET cluster_id=?, cluster_label=?, bio_theme_primary=? WHERE startup_id=?',
                (new_cl, LABELS[new_cl], new_bio, startup_id))
    log(startup_id, 'cluster_id', old_cl, new_cl, reason)
    if old_bio != new_bio:
        log(startup_id, 'bio_theme_primary', old_bio, new_bio, reason)
    print(f'  move OK {name}: CL{old_cl}->CL{new_cl}  bio: {old_bio} -> {new_bio}')

print('=== CL5 Food — bio_theme fixes ===')
fix_bio('levya',               'Food Systems & Alt Proteins', 'precision fermentation fats/oils for food ingredients -> Food Systems')
fix_bio('nat4bio',             'Food Systems & Alt Proteins', 'edible coatings for food protection -> Food Systems, not Biomaterials')
fix_bio('nutrition-from-water','Food Systems & Alt Proteins', 'microalgae protein as whey replacement -> Food Systems, not Biomaterials')
fix_bio('savefruit',           'Food Systems & Alt Proteins', 'post-harvest nanotech coatings for produce shelf-life -> Food Systems')
fix_bio('rnatech-ar',          'Food Systems & Alt Proteins', 'RNA bioactive functional ingredients for supplements/food -> Food Systems')

print('\n=== CL5 → CL3: vacunas/tratamientos animales acuáticos ===')
move_cluster('aquit',     3, 'Bioinputs & Crop Resilience', 'fish immunity treatments -> Ag Biologicals CL3 (animal health bioinput)')
move_cluster('werk-nvac', 3, 'Bioinputs & Crop Resilience', 'saRNA fish vaccine -> Ag Biologicals CL3 (animal health bioinput)')

print('\n=== CL3 Ag Biologicals — bio_theme fixes ===')
fix_bio('unibaio',    'Bioinputs & Crop Resilience', 'natural microparticles for agroinput performance -> Bioinputs, not Biomaterials')
fix_bio('zavia-bio',  'Bioinputs & Crop Resilience', 'biological agro-inputs for resilient agriculture -> Bioinputs, not Biomaterials')
fix_bio('syocin',     'Bioinputs & Crop Resilience', 'protein biobactericides to protect crops -> Bioinputs, not Biomaterials')
fix_bio('idealab-br', 'Bioinputs & Crop Resilience', 'bioinputs CDMO with microbial prospecting -> Bioinputs, not Biomaterials')
fix_bio('caligenia',  'Bioinputs & Crop Resilience', 'BACTERCHAR soil amendment (biochar+bacteria) -> Bioinputs, not Nature')
fix_bio('exacta-bioscience', 'Bioinputs & Crop Resilience', 'bacteriophage-based crop protection -> Bioinputs, not Farm Intelligence')

print('\n=== CL3 → CL5: food companies misplaced in Ag Biologicals ===')
move_cluster('updairy',           5, 'Food Systems & Alt Proteins', 'precision fermentation dairy proteins -> Food Systems CL5')
move_cluster('future-cow',        5, 'Food Systems & Alt Proteins', 'animal-free dairy proteins via precision fermentation -> Food Systems CL5')
move_cluster('harmony-br',        5, 'Food Systems & Alt Proteins', 'infant nutrition via precision fermentation -> Food Systems CL5')
move_cluster('the-live-green-co', 5, 'Food Systems & Alt Proteins', 'AI plant-based ingredient replacement -> Food Systems CL5')
move_cluster('food-for-the-future-cl', 5, 'Food Systems & Alt Proteins', 'insect bioconversion for food protein -> Food Systems CL5')
move_cluster('atarraya',          5, 'Food Systems & Alt Proteins', 'containerized AI aquaculture production -> Food Systems CL5')
move_cluster('bruna-altum-lab',   5, 'Food Systems & Alt Proteins', 'AI raw material quality for food production -> Food Systems CL5')

print('\n=== CL3 → CL6: biomanufacturing companies ===')
move_cluster('biolinker',      6, 'Biomanufacturing & Fermentation Economy', 'synthetic biology protein engineering tools -> Biomanufacturing CL6')
move_cluster('neoprospecta-br',6, 'Biomanufacturing & Fermentation Economy', 'microbial contamination mapping with DNA sequencing -> Biomanufacturing CL6')

print('\n=== CL3 → CL4: Farm Intelligence modeling platforms ===')
move_cluster('calice',      4, 'Farm Intelligence', 'G×E×M crop modeling platform -> Farm Intelligence CL4')
move_cluster('calice-ai-ar',4, 'Farm Intelligence', 'probabilistic crop performance simulation platform -> Farm Intelligence CL4')

conn.commit()
print('\n=== Regenerando dashboard JS ===')
import sys as _sys; _sys.path.insert(0, '.')
from src.clustering import write_dashboard_data
write_dashboard_data(conn)
conn.close()
print('Listo.')
