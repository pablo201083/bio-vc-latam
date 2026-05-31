import sqlite3, pathlib, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
db = pathlib.Path('db/bio_latam.db')
conn = sqlite3.connect(db)
cur = conn.cursor()

for cl_id, cl_name, expected_bios in [
    (7, 'Nature/Climate',   ['Nature & Ecosystem Tech']),
    (8, 'Biomaterials',     ['Biomaterials & Circular Economy']),
    (6, 'Biomanufacturing', ['Biomanufacturing & Fermentation Economy']),
    (4, 'Farm Intelligence',['Farm Intelligence', 'Nature & Ecosystem Tech']),
]:
    cur.execute("""
        SELECT e.canonical_name, e.country_code, sx.bio_theme_primary,
               sx.cluster_confidence, sx.is_outlier,
               sx.startup_id,
               substr(coalesce(sx.startup_summary_en, sx.startup_summary_v1,''),1,130)
        FROM startup_extended sx JOIN entities e ON e.entity_id=sx.startup_id
        WHERE sx.scope_decision='include' AND sx.cluster_id=?
        ORDER BY sx.is_outlier DESC, sx.bio_theme_primary, sx.cluster_confidence
    """, (cl_id,))
    rows = cur.fetchall()
    mismatches = [r for r in rows if r[2] not in expected_bios]
    outliers    = [r for r in rows if r[4]]
    print(f'\n{"="*72}')
    print(f'CL{cl_id} {cl_name} — {len(rows)} startups | {len(outliers)} outliers | {len(mismatches)} BT mismatch')
    print(f'{"="*72}')
    if mismatches:
        print('  -- BT mismatches --')
        for r in mismatches:
            name, cc, bio, conf, outlier, sid, summ = r
            flag = '[OUT]' if outlier else '     '
            print(f'  {flag} [{conf:.2f}] {name} ({cc}) — bio={bio}')
            print(f'           id={sid}')
            print(f'           {summ}')
    if outliers:
        correct_outliers = [r for r in outliers if r[2] in expected_bios]
        if correct_outliers:
            print(f'  -- Outliers with correct BT ({len(correct_outliers)}) --')
            for r in correct_outliers:
                name, cc, bio, conf, _, sid, summ = r
                print(f'  [OUT] [{conf:.2f}] {name} ({cc}) — {summ[:100]}')

conn.close()
