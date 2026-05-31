import sqlite3, pathlib, sys, datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
db = pathlib.Path('db/bio_latam.db')
conn = sqlite3.connect(db)
cur = conn.cursor()
now = datetime.datetime.now(datetime.UTC).isoformat()

LABELS = {
    3: 'Ag Biologicals & Bioinputs||biologicals · bioinputs · crop resilience · microbial',
    5: 'Food Systems & Alt Proteins||food biotech · alt proteins · novel ingredients · functional',
}

def log(entity_id, field, old_val, new_val, reason):
    cur.execute(
        '''INSERT INTO audit_log (timestamp, actor, entity_id, table_name, field, old_value, new_value, reason)
           VALUES (?,?,?,?,?,?,?,?)''',
        (now, 'human:curador', entity_id, 'startup_extended', field,
         str(old_val) if old_val else None, str(new_val), reason))

def fix_bio(sid, new_bio, reason):
    cur.execute('SELECT bio_theme_primary, canonical_name FROM startup_extended sx '
                'JOIN entities e ON e.entity_id=sx.startup_id WHERE sx.startup_id=?', (sid,))
    row = cur.fetchone()
    if not row: print(f'  NOT FOUND: {sid}'); return
    old_bio, name = row
    if old_bio == new_bio: print(f'  SKIP {name}: already {new_bio}'); return
    cur.execute('UPDATE startup_extended SET bio_theme_primary=? WHERE startup_id=?', (new_bio, sid))
    log(sid, 'bio_theme_primary', old_bio, new_bio, reason)
    print(f'  bio OK  {name}: {old_bio} -> {new_bio}')

def move_cluster(sid, new_cl, new_bio, reason):
    cur.execute('SELECT cluster_id, bio_theme_primary, canonical_name FROM startup_extended sx '
                'JOIN entities e ON e.entity_id=sx.startup_id WHERE sx.startup_id=?', (sid,))
    row = cur.fetchone()
    if not row: print(f'  NOT FOUND: {sid}'); return
    old_cl, old_bio, name = row
    cur.execute('UPDATE startup_extended SET cluster_id=?, cluster_label=?, bio_theme_primary=? WHERE startup_id=?',
                (new_cl, LABELS[new_cl], new_bio, sid))
    log(sid, 'cluster_id', old_cl, new_cl, reason)
    if old_bio != new_bio:
        log(sid, 'bio_theme_primary', old_bio, new_bio, reason)
    print(f'  move OK {name}: CL{old_cl}->CL{new_cl}')

print('=== CL5 bio_theme fixes (IDs corregidos) ===')
fix_bio('nutrition-from-water-cl', 'Food Systems & Alt Proteins', 'microalgae protein as whey replacement -> Food Systems')
fix_bio('savefruit-mx',            'Food Systems & Alt Proteins', 'post-harvest nanotech coatings for produce -> Food Systems')

print('\n=== CL3 bio_theme fixes (IDs corregidos) ===')
fix_bio('zavia_bio',          'Bioinputs & Crop Resilience', 'biological agro-inputs -> Bioinputs, not Biomaterials')
fix_bio('syocin-biotech',     'Bioinputs & Crop Resilience', 'protein biobactericides to protect crops -> Bioinputs, not Biomaterials')
fix_bio('ideelab',            'Bioinputs & Crop Resilience', 'bioinputs CDMO -> Bioinputs, not Biomaterials')
fix_bio('exacta-bioscience-cl','Bioinputs & Crop Resilience', 'bacteriophage-based crop protection -> Bioinputs, not Farm Intelligence')

print('\n=== CL3 → CL5: food companies misplaced (IDs corregidos) ===')
move_cluster('future_cow',            5, 'Food Systems & Alt Proteins', 'animal-free dairy proteins via precision fermentation -> Food Systems CL5')
move_cluster('harmony-biosciences',   5, 'Food Systems & Alt Proteins', 'infant nutrition via precision fermentation -> Food Systems CL5')
move_cluster('the-live-green-co-cl',  5, 'Food Systems & Alt Proteins', 'AI plant-based ingredient replacement -> Food Systems CL5')
move_cluster('atarraya-mx',           5, 'Food Systems & Alt Proteins', 'containerized AI aquaculture food production -> Food Systems CL5')
move_cluster('bruna-by-altum-lab-cl', 5, 'Food Systems & Alt Proteins', 'AI raw material quality for food production -> Food Systems CL5')

conn.commit()
print('\n=== Regenerando dashboard JS ===')
import sys as _sys; _sys.path.insert(0, '.')
from src.clustering import write_dashboard_data
write_dashboard_data(conn)
conn.close()
print('Listo.')
