import sqlite3, pathlib, sys, math
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
conn = sqlite3.connect('db/bio_latam.db')
cur = conn.cursor()

# Centroide por bio_theme (solo no-outliers)
cur.execute("""
    SELECT sx.bio_theme_primary,
           avg(sx.umap_x) as cx, avg(sx.umap_y) as cy
    FROM startup_extended sx
    WHERE scope_decision='include' AND is_outlier=0
    GROUP BY sx.bio_theme_primary
""")
centroids = {r[0]: (r[1], r[2]) for r in cur.fetchall()}

# Todos los outliers con su distancia al centroide de su bio_theme
cur.execute("""
    SELECT e.canonical_name, sx.startup_id, sx.bio_theme_primary,
           sx.umap_x, sx.umap_y, sx.cluster_confidence, sx.cluster_label
    FROM startup_extended sx JOIN entities e ON e.entity_id=sx.startup_id
    WHERE sx.scope_decision='include' AND sx.is_outlier=1
    ORDER BY sx.bio_theme_primary
""")
rows = cur.fetchall()

results = []
for name, sid, bio, ux, uy, conf, lbl in rows:
    if bio not in centroids: continue
    cx, cy = centroids[bio]
    dist = math.sqrt((ux-cx)**2 + (uy-cy)**2)
    results.append((dist, name, sid, bio, conf, lbl))

results.sort(reverse=True)
print(f'Top outliers mas alejados de su centroide de bio_theme:')
print(f'{"Dist":>6}  {"Conf":>5}  {"Startup":<32}  {"Bio_theme":<36}  Cluster')
print('-'*125)
for dist, name, sid, bio, conf, lbl in results[:25]:
    cl_short = lbl.split('||')[0] if lbl else '—'
    flag = ' *** REVISAR' if dist > 8 else (' *' if dist > 5 else '')
    print(f'{dist:6.1f}  {conf:5.2f}  {name:<32}  {bio:<36}  {cl_short}{flag}')

print(f'\nTotal outliers: {len(results)}')
conn.close()
