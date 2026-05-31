"""
include_adjacent.py
--------------------
Incluye 11 empresas bio-adyacentes del review list en el dashboard.

Criterio: adyacencia directa al ecosistema bio —
  salud digital con componente diagnóstico/clínico real,
  agricultura de precisión con sensórica/datos agronómicos,
  salud animal con servicios clínicos.

Por cada empresa:
  - scope_decision → 'include', scope_status → 'confirmed'
  - bio_theme_primary asignado
  - tech_depth asignado (deep / applied / enabler)
  - cluster_label asignado (sub-label de adyacencia)
  - sub_cluster_label
  - umap_x / umap_y = centroide del tema + jitter determinístico
  - is_outlier = 1 (no pertenecen a ningún cluster HDBSCAN)
  - Audit log

Ejecutar:
  .venv/Scripts/python.exe include_adjacent.py
"""

import sqlite3, pathlib, datetime, sys, hashlib
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

db   = pathlib.Path('db/bio_latam.db')
conn = sqlite3.connect(db)
cur  = conn.cursor()
now  = datetime.datetime.now(datetime.UTC).isoformat()

REASON = ('include_adjacent.py: incluida por adyacencia directa al ecosistema bio LATAM. '
          'Posición UMAP = centroide del tema + jitter determinístico. is_outlier=1.')

# ─── Centroides UMAP por tema ─────────────────────────────────────────────────
rows = cur.execute('''
    SELECT bio_theme_primary, umap_x, umap_y
    FROM startup_extended
    WHERE scope_decision='include' AND umap_x IS NOT NULL AND bio_theme_primary IS NOT NULL
''').fetchall()
from collections import defaultdict
theme_pts = defaultdict(list)
for t, x, y in rows:
    theme_pts[t].append((x, y))
CENTROIDS = {t: (sum(p[0] for p in pts)/len(pts), sum(p[1] for p in pts)/len(pts))
             for t, pts in theme_pts.items()}

def jitter(eid, scale=0.45):
    """Jitter determinístico basado en hash del entity_id."""
    h = int(hashlib.md5(eid.encode()).hexdigest()[:8], 16)
    dx = ((h % 1000) / 1000.0 - 0.5) * scale * 2
    dy = (((h // 1000) % 1000) / 1000.0 - 0.5) * scale * 2
    return dx, dy

def umap_pos(eid, theme):
    cx, cy = CENTROIDS.get(theme, (0.0, 0.0))
    dx, dy = jitter(eid)
    return round(cx + dx, 3), round(cy + dy, 3)

# ─── Empresas a incluir ───────────────────────────────────────────────────────
# (entity_id, bio_theme, tech_depth, sub_cluster_label, cluster_label_suffix, keywords)
INCLUSIONS = [
    # ── Ya tienen bio_theme del paso anterior ──────────────────────────────────
    ('examedi-cl',
     'Diagnostics & Health Access', 'deep',
     'Point-of-Care & Home Diagnostics',
     'Diagnostics & Health Access — Point-of-Care & Home Diagnostics',
     'home diagnostics · lab testing · point-of-care · medical access'),

    ('avedian-ar',
     'Diagnostics & Health Access', 'deep',
     'Digital Health & Medtech',
     'Diagnostics & Health Access — Digital Health & Medtech',
     'ai · health records · predictive · hospital · clinical'),

    ('movet-co',
     'Bioinputs & Crop Resilience', 'applied',
     'Animal Health & Bioinputs',
     'Bioinputs & Crop Resilience — Animal Health & Bioinputs',
     'veterinary · animal health · clinics · livestock · standardized'),

    # ── Sin bio_theme aún ─────────────────────────────────────────────────────
    ('beep-saude',
     'Diagnostics & Health Access', 'applied',
     'Point-of-Care & Home Diagnostics',
     'Diagnostics & Health Access — Point-of-Care & Home Diagnostics',
     'home health · lab tests · nursing · medical access'),

    ('genial-care',
     'Diagnostics & Health Access', 'applied',
     'Digital Health & Medtech',
     'Diagnostics & Health Access — Digital Health & Medtech',
     'autism · behavioral therapy · digital health · clinical platform'),

    ('koltin',
     'Diagnostics & Health Access', 'applied',
     'Digital Health & Medtech',
     'Diagnostics & Health Access — Digital Health & Medtech',
     'diabetes · chronic condition · digital health · patient management'),

    ('bloomcare',
     'Diagnostics & Health Access', 'applied',
     'Digital Health & Medtech',
     'Diagnostics & Health Access — Digital Health & Medtech',
     'maternal health · pregnancy · women health · digital platform'),

    ('motivia-ar',
     'Diagnostics & Health Access', 'applied',
     'Digital Health & Medtech',
     'Diagnostics & Health Access — Digital Health & Medtech',
     'medication adherence · chronic disease · behavioral science · ai'),

    ('isobar-br',
     'Farm Intelligence', 'applied',
     'Agronomic',
     'Farm Intelligence — Agronomic',
     'precision agriculture · coffee · sugarcane · microclimate · analytics'),

    ('farmbox',
     'Farm Intelligence', 'applied',
     'Agronomic',
     'Farm Intelligence — Agronomic',
     'agronomy · crop planning · monitoring · agricultural operations'),

    ('wiseconn-chile',
     'Farm Intelligence', 'applied',
     'Agronomic',
     'Farm Intelligence — Agronomic',
     'irrigation · water · automation · sensors · monitoring'),
]

print(f'=== include_adjacent.py — {len(INCLUSIONS)} empresas ===\n')

applied = 0
for tup in INCLUSIONS:
    eid, theme, depth, sub_cl, cl_prefix, keywords = tup
    cl_label = cl_prefix + '||' + keywords

    # Verificar que existe en entities
    r = cur.execute('''
        SELECT e.entity_id, e.canonical_name, sx.scope_decision, sx.bio_theme_primary
        FROM startup_extended sx JOIN entities e ON e.entity_id=sx.startup_id
        WHERE e.entity_id=?
    ''', (eid,)).fetchone()

    if not r:
        # Buscar por nombre aproximado
        keyword = eid.split('-')[0]
        r = cur.execute('''
            SELECT e.entity_id, e.canonical_name, sx.scope_decision, sx.bio_theme_primary
            FROM startup_extended sx JOIN entities e ON e.entity_id=sx.startup_id
            WHERE LOWER(e.canonical_name) LIKE ? OR LOWER(e.entity_id) LIKE ?
        ''', (f'%{keyword}%', f'%{keyword}%')).fetchone()

    if not r:
        print(f'  NOT FOUND: {eid}')
        continue

    real_eid, name, old_scope, old_theme = r
    ux, uy = umap_pos(real_eid, theme)

    # Actualizar startup_extended
    cur.execute('''
        UPDATE startup_extended SET
            scope_decision      = 'include',
            scope_status        = 'confirmed',
            bio_theme_primary   = ?,
            bio_theme_confidence= 0.78,
            tech_depth          = ?,
            tech_depth_confidence = 0.74,
            tech_depth_basis    = ?,
            cluster_label       = ?,
            sub_cluster_label   = ?,
            umap_x              = ?,
            umap_y              = ?,
            is_outlier          = 1,
            is_bio_universe     = 1
        WHERE startup_id = ?
    ''', (
        theme, depth,
        f'include_adjacent.py: {depth} — adyacencia directa a {theme}',
        cl_label, sub_cl, ux, uy, real_eid
    ))

    # Audit log
    for field, old_val, new_val in [
        ('scope_decision', old_scope, 'include'),
        ('bio_theme_primary', old_theme, theme),
        ('tech_depth', None, depth),
        ('cluster_label', None, cl_label),
        ('umap_x', None, ux),
        ('umap_y', None, uy),
    ]:
        cur.execute('''INSERT INTO audit_log
                         (timestamp,actor,entity_id,table_name,field,old_value,new_value,reason)
                       VALUES (?,?,?,?,?,?,?,?)''',
                    (now,'human:curador',real_eid,'startup_extended',field,
                     str(old_val) if old_val is not None else None,
                     str(new_val), REASON))

    depth_icon = {'deep':'🔬','applied':'⚙️','enabler':'💻'}.get(depth,'•')
    print(f'  {depth_icon} {name[:30]:<32}  {theme[:30]:<32}  depth={depth:<8}  umap=({ux:+.2f},{uy:+.2f})')
    applied += 1

conn.commit()
conn.close()
print(f'\n✓ {applied}/{len(INCLUSIONS)} empresas incluidas en el dashboard.')
print('\nProximo paso: regenerar startup-themes-data.js')
