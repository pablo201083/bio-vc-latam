import sqlite3, pathlib

db = pathlib.Path('db/bio_latam.db')
conn = sqlite3.connect(db)
cur = conn.cursor()

cluster_labels = {
    0: 'Therapeutics-Regen', 1: 'Drug Discovery', 2: 'Diagnostics',
    3: 'Ag Biologicals', 4: 'Farm Intelligence', 5: 'Food Systems',
    6: 'Biomanufacturing', 7: 'Nature/Climate', 8: 'Biomaterials',
}

expected = {
    0: ['Therapeutics'],
    1: ['Therapeutics', 'Diagnostics & Health Access'],
    2: ['Diagnostics & Health Access'],
    3: ['Bioinputs & Crop Resilience'],
    4: ['Farm Intelligence', 'Nature & Ecosystem Tech'],
    5: ['Food Systems & Alt Proteins'],
    6: ['Biomanufacturing & Fermentation Economy'],
    7: ['Nature & Ecosystem Tech', 'Biomaterials & Circular Economy'],
    8: ['Biomaterials & Circular Economy'],
}

baseline = {
    0: (41, 7, 92), 1: (60, 20, 53), 2: (37, 10, 97), 3: (54, 14, 75),
    4: (60, 36, 50), 5: (28, 17, 89), 6: (13, 15, 76), 7: (46, 21, 80), 8: (34, 8, 73),
}

print('CLUSTER METRICS — post curacion iteracion 1')
print(f'  CL  N(delta)  Periph%  BT%(delta)  Name')
print('  ' + '-' * 65)

total_n, total_periph = 0, 0
for cl in range(9):
    cur.execute(
        "SELECT count(*) FROM startup_extended WHERE scope_decision='include' AND cluster_id=?", (cl,))
    n = cur.fetchone()[0]
    cur.execute(
        "SELECT count(*) FROM startup_extended WHERE scope_decision='include' AND cluster_id=? AND is_outlier=1", (cl,))
    periph = cur.fetchone()[0]
    cur.execute(
        "SELECT bio_theme_primary FROM startup_extended WHERE scope_decision='include' AND cluster_id=?", (cl,))
    bios = [r[0] for r in cur.fetchall()]
    exp = expected.get(cl, [])
    bt_ok = sum(1 for b in bios if b in exp)
    bt_pct = int(bt_ok / n * 100) if n else 0
    periph_pct = int(periph / n * 100) if n else 0

    b_n, b_periph, b_bt = baseline[cl]
    n_delta = f'{n - b_n:+d}'
    bt_delta = f'{bt_pct - b_bt:+d}pp'
    name = cluster_labels.get(cl, '?')
    print(f'  {cl}  {n:3d}({n_delta:3s})   {periph_pct:3d}%    {bt_pct:3d}%({bt_delta:6s})  {name}')
    total_n += n
    total_periph += periph

print('  ' + '-' * 65)
print(f'  Total: {total_n}, periphery {total_periph}/{total_n} = {int(total_periph/total_n*100)}%')
conn.close()
