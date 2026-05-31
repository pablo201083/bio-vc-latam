import sqlite3, pathlib, sys, datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
db = pathlib.Path('db/bio_latam.db')
conn = sqlite3.connect(db)
cur = conn.cursor()
now = datetime.datetime.now(datetime.UTC).isoformat()

LABELS = {
    1: 'Therapeutics — Drug Discovery & Development||drug discovery · oncology · therapeutics · small molecule',
    3: 'Ag Biologicals & Bioinputs||biologicals · bioinputs · crop resilience · microbial',
    4: 'Farm Intelligence & Precision Agriculture||precision agriculture · agtech · satellite · AI',
    5: 'Food Systems & Alt Proteins||food biotech · alt proteins · novel ingredients · functional',
    6: 'Biomanufacturing & Precision Fermentation||fermentation · synthetic biology · biomanufacturing · platform',
    8: 'Biomaterials & Circular Chemistry||biomaterials · biobased · circular · sustainable',
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
    if old_bio == new_bio: print(f'  SKIP {name}'); return
    cur.execute('UPDATE startup_extended SET bio_theme_primary=? WHERE startup_id=?', (new_bio, sid))
    log(sid, 'bio_theme_primary', old_bio, new_bio, reason)
    print(f'  bio  {name}: {old_bio} -> {new_bio}')

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
    print(f'  move {name}: CL{old_cl}->CL{new_cl}  bio={new_bio}')

# ── CL7 Nature/Climate — bio_theme fixes (cluster correcto, dato malo) ──────
print('=== CL7 Nature/Climate — bio_theme fixes ===')
BIO_NAT = 'Nature & Ecosystem Tech'
fix_bio('agrojusto',    BIO_NAT, 'digital infrastructure for local food systems/territorial value chains -> Nature')
fix_bio('siloreal',     BIO_NAT, 'remotely verify and digitalize agricultural assets for finance/insurance -> Nature')
fix_bio('branch_energy',BIO_NAT, 'clean-energy/energy-management infrastructure -> Nature, not Diagnostics')
fix_bio('agrotools',    BIO_NAT, 'agribusiness intelligence connecting land, supply chains, ESG -> Nature')
fix_bio('culttivo',     BIO_NAT, 'coffee-finance + satellite + ESG/climate-risk intelligence -> Nature')
fix_bio('traive',       BIO_NAT, 'AI agricultural credit, risk, ESG analytics -> Nature/Climate finance')
fix_bio('ucrop-it-ar',  BIO_NAT, 'satellite deforestation monitoring + EUDR compliance -> Nature')
fix_bio('ecotrace-br',  BIO_NAT, 'agribusiness traceability for sustainability compliance -> Nature')
fix_bio('earth-ocean-farms-mx', BIO_NAT, 'regenerative marine aquaculture conservation -> Nature')

# CL7 cluster moves
print()
move_cluster('brain_ag', 4, 'Farm Intelligence',             'agribusiness data/credit intelligence -> Farm Intelligence CL4')
move_cluster('muta',     8, 'Biomaterials & Circular Economy','circular economy recyclables B2B -> Biomaterials CL8')

# ── CL8 Biomaterials — bio_theme fixes ──────────────────────────────────────
print('\n=== CL8 Biomaterials — bio_theme fixes ===')
BIO_MAT = 'Biomaterials & Circular Economy'
fix_bio('living-ink-us', BIO_MAT, 'algae-based bio-pigments as petroleum replacement -> Biomaterials')
fix_bio('michroma',      BIO_MAT, 'natural colorants via fungal synthetic biology -> Biomaterials, not Food')
fix_bio('ages',          BIO_MAT, 'bioactive molecules from Amazon for longevity -> Biomaterials, not Nature')
fix_bio('giraffe-bio-ar',BIO_MAT, 'custom biomolecules for copper/lithium leaching -> Biomaterials industrial')
fix_bio('HIAMET',        BIO_MAT, 'improving biogas production from organic waste -> Biomaterials/Circular')
fix_bio('cyanomin',      BIO_MAT, 'biological desalination with cyanobacteria -> Biomaterials, not Nature')
fix_bio('alkemio',       BIO_MAT, 'rare earth separation/refining with clean chemistry -> Biomaterials')

# CL8 cluster moves
print()
move_cluster('stamm-ar', 6, 'Biomanufacturing & Fermentation Economy', 'high-throughput bioprocessors for biomanufacturing -> CL6')
move_cluster('neocell',  6, 'Biomanufacturing & Fermentation Economy', 'biosimilar/biologic manufacturing -> Biomanufacturing CL6')

# ── CL4 Farm Intelligence — bio_theme fixes ──────────────────────────────────
print('\n=== CL4 Farm Intelligence — bio_theme fixes ===')
BIO_FARM = 'Farm Intelligence'
fix_bio('tbit',      BIO_FARM, 'digital image processing + AI for seed/grain analysis -> Farm Intelligence')
fix_bio('cerradox',  BIO_FARM, 'technology-monitored agricultural production platform -> Farm Intelligence')
fix_bio('beeflow',   BIO_FARM, 'bee nutrition + pollination analytics platform -> Farm Intelligence')
fix_bio('wiagro',    BIO_FARM, 'IoT + satellite grain monitoring + predictive models -> Farm Intelligence')

# CL4 → CL5: food companies misplaced
print()
move_cluster('nude',         5, 'Food Systems & Alt Proteins', 'plant-based oat foods/beverages -> Food Systems CL5')
move_cluster('frizata',      5, 'Food Systems & Alt Proteins', 'flexitarian frozen food brand -> Food Systems CL5')
move_cluster('nocarbon_milk',5, 'Food Systems & Alt Proteins', 'carbon-neutral organic dairy brand -> Food Systems CL5')

# CL4 → CL3: bioinput outliers (conf=0.35)
print()
move_cluster('bioin-br',   3, 'Bioinputs & Crop Resilience', 'biocontrol cards + pest monitoring -> Ag Biologicals CL3')
move_cluster('seedmatriz', 3, 'Bioinputs & Crop Resilience', 'seed encapsulation technology -> Ag Biologicals CL3')
move_cluster('nanotica',   3, 'Bioinputs & Crop Resilience', 'nanoencapsulation for crop inputs -> Ag Biologicals CL3')

# CL4 → CL1: protein analysis tool (wrong domain entirely)
print()
move_cluster('geoprot', 1, 'Therapeutics', 'protein function analysis/prediction tool -> Drug Discovery CL1')

conn.commit()
print('\n=== Regenerando dashboard JS ===')
import sys as _sys; _sys.path.insert(0, '.')
from src.clustering import write_dashboard_data
write_dashboard_data(conn)
conn.close()
print('Listo.')
