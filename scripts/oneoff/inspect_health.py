import sqlite3, pathlib, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
db = pathlib.Path('db/bio_latam.db')
conn = sqlite3.connect(db)
cur = conn.cursor()

print('=== CL0 Therapeutics-Regen vs CL1 Drug Discovery vs CL2 Diagnostics ===')
print('Foco: empresas en el borde y distribucion UMAP\n')

# UMAP distribution per cluster
for cl_id, name in [(0,'Therapeutics-Regen'), (1,'Drug Discovery'), (2,'Diagnostics')]:
    cur.execute("""
        SELECT round(avg(sx.umap_x),2), round(avg(sx.umap_y),2),
               round(min(sx.umap_x),2), round(max(sx.umap_x),2),
               round(min(sx.umap_y),2), round(max(sx.umap_y),2),
               count(*)
        FROM startup_extended sx
        WHERE scope_decision='include' AND cluster_id=?
    """, (cl_id,))
    r = cur.fetchone()
    print(f'CL{cl_id} {name}: centroid=({r[0]},{r[1]})  x=[{r[2]},{r[3]}]  y=[{r[4]},{r[5]}]  n={r[6]}')

print()

# Companies crossing the boundary: in CL0/CL1 with bio=Diagnostics, or in CL2 with bio=Therapeutics
cur.execute("""
    SELECT e.canonical_name, e.country_code, sx.cluster_id, sx.bio_theme_primary,
           sx.cluster_confidence, sx.is_outlier, sx.umap_x, sx.umap_y,
           substr(coalesce(sx.startup_summary_en, sx.startup_summary_v1,''),1,150)
    FROM startup_extended sx JOIN entities e ON e.entity_id=sx.startup_id
    WHERE sx.scope_decision='include'
      AND sx.cluster_id IN (0,1,2)
      AND (
        (sx.cluster_id IN (0,1) AND sx.bio_theme_primary = 'Diagnostics & Health Access')
        OR (sx.cluster_id = 2 AND sx.bio_theme_primary = 'Therapeutics')
      )
    ORDER BY sx.cluster_id, sx.cluster_confidence DESC
""")
rows = cur.fetchall()
print(f'Empresas en la frontera Therapeutics/Diagnostics: {len(rows)}')
print()
current_cl = None
for name, cc, cl, bio, conf, outlier, ux, uy, summ in rows:
    if cl != current_cl:
        current_cl = cl
        labels = {0:'Therapeutics-Regen', 1:'Drug Discovery', 2:'Diagnostics'}
        print(f'  --- En CL{cl} ({labels[cl]}) con bio={bio} ---')
    flag = '[OUT]' if outlier else '     '
    print(f'  {flag} [{conf:.2f}] {name} ({cc})  umap=({ux:.1f},{uy:.1f})')
    print(f'         {summ}')
    print()

# Bimodality check: within CL1, are there two sub-groups?
print('\n=== CL1 Drug Discovery — distribucion por bio_theme ===')
cur.execute("""
    SELECT sx.bio_theme_primary, count(*), round(avg(sx.umap_x),2), round(avg(sx.umap_y),2),
           round(avg(sx.cluster_confidence),2)
    FROM startup_extended sx
    WHERE scope_decision='include' AND cluster_id=1
    GROUP BY sx.bio_theme_primary
    ORDER BY count(*) DESC
""")
for bio, n, cx, cy, avg_conf in cur.fetchall():
    print(f'  {n:3d}  centroid=({cx},{cy})  avg_conf={avg_conf}  {bio}')

conn.close()
