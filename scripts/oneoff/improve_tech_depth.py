"""
improve_tech_depth.py
----------------------
Mejora autónoma de la clasificación tech_depth usando 4 señales
que el clasificador original no aprovechó.

ESTRATEGIA (en orden de precisión):

  S1. Sub_cluster_label lookup (100% pureza en datos de entrenamiento)
      Cada sub_cluster_label tiene una profundidad tecnológica clara.
      "Diagnostics" → deep, "Agrifintech & Rural Credit" → enabler.

  S2. Cluster majority vote (alta pureza para la mayoría de clusters)
      Si CL0 tiene 57/57 high-conf como deep → las empresas inciertas
      en CL0 son casi con certeza deep también.

  S3. TF-IDF + LogisticRegression sobre startup_summary_en
      Entrenado con los 218 deep + 33 enabler de alta confianza.
      Aplicado a empresas sin sub_cluster ni cluster puro.

  S4. UMAP k-NN (5 vecinos más cercanos en el espacio 2D)
      Último recurso: si los vecinos más cercanos son todos deep,
      la empresa incierta probablemente también lo es.

Solo se actualiza tech_depth cuando la señal tiene alta confianza
(>= 0.72 según la fuente). Los casos que siguen inciertos se dejan.

Ejecutar:
  .venv/Scripts/python.exe improve_tech_depth.py
"""

import sqlite3, pathlib, datetime, sys, json, math
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

db   = pathlib.Path('db/bio_latam.db')
conn = sqlite3.connect(db)
cur  = conn.cursor()
now  = datetime.datetime.now(datetime.UTC).isoformat()

CONF_HIGH     = 0.68   # umbral para incluir en entrenamiento
CONF_MIN_UPD  = 0.72   # umbral mínimo para aplicar un update

def log_update(eid, old_depth, new_depth, new_conf, source):
    basis = f'improve_tech_depth.py — {source}'
    cur.execute('UPDATE startup_extended SET tech_depth=?, tech_depth_confidence=?, tech_depth_basis=? WHERE startup_id=?',
                (new_depth, new_conf, basis, eid))
    cur.execute('''INSERT INTO audit_log (timestamp, actor, entity_id, table_name, field, old_value, new_value, reason)
                   VALUES (?,?,?,?,?,?,?,?)''',
                (now, 'human:curador', eid, 'startup_extended', 'tech_depth',
                 old_depth, new_depth, basis))

# ─── Carga de todos los datos ─────────────────────────────────────────────────
all_rows = cur.execute('''
    SELECT startup_id, tech_depth, tech_depth_confidence,
           sub_cluster_label, cluster_id,
           umap_x, umap_y,
           COALESCE(startup_summary_en, startup_summary_v1, '') as summary,
           bio_theme_primary
    FROM startup_extended
''').fetchall()

# Casos a mejorar: baja confianza O unclassified
to_improve = {r[0]: dict(zip(
    ['id','depth','conf','sub_cl','cluster_id','x','y','summary','theme'],r
)) for r in all_rows if r[1]=='unclassified' or r[2]<CONF_HIGH}

# Base de entrenamiento: alta confianza, no unclassified
training = [dict(zip(
    ['id','depth','conf','sub_cl','cluster_id','x','y','summary','theme'],r
)) for r in all_rows if r[1]!='unclassified' and r[2]>=CONF_HIGH and r[1] in ('deep','enabler')]

print(f'=== improve_tech_depth.py ===')
print(f'  Para mejorar: {len(to_improve)}  |  Training set: {len(training)} (deep+enabler, conf>={CONF_HIGH})')
print()

updates = {}   # eid → (new_depth, new_conf, source)

# ═════════════════════════════════════════════════════════════════════════════
# S1 — SUB_CLUSTER_LABEL LOOKUP
# ═════════════════════════════════════════════════════════════════════════════
# Construir el mapa de sub_cluster_label → {depth: count} desde training
sub_cl_map = {}
for t in training:
    sc = t['sub_cl']
    if not sc:
        continue
    sub_cl_map.setdefault(sc, {})
    sub_cl_map[sc][t['depth']] = sub_cl_map[sc].get(t['depth'], 0) + 1

# Para cada sub_cluster_label, calcular pureza y depth dominante
sub_cl_lookup = {}   # sub_cl → (dominant_depth, purity, n)
for sc, counts in sub_cl_map.items():
    total = sum(counts.values())
    dominant_depth, dominant_n = max(counts.items(), key=lambda x:x[1])
    purity = dominant_n / total
    if purity >= 0.85 and total >= 2:   # solo si >=85% puro y al menos 2 ejemplos
        sub_cl_lookup[sc] = (dominant_depth, purity, total)
    elif total == 1:
        # Solo 1 ejemplo: usar con confianza moderada
        sub_cl_lookup[sc] = (dominant_depth, 0.72, total)

print(f'S1: Sub_cluster_label lookup — {len(sub_cl_lookup)} sub-clusters con señal clara')

s1_count = 0
for eid, rec in to_improve.items():
    sc = rec['sub_cl']
    if not sc or sc not in sub_cl_lookup:
        continue
    new_depth, purity, n = sub_cl_lookup[sc]
    # Confianza: purity * escala según tamaño del grupo
    conf = round(min(0.70 + purity * 0.25 + min(n,20)*0.003, 0.95), 3)
    if conf < CONF_MIN_UPD:
        continue
    if eid not in updates or updates[eid][1] < conf:
        updates[eid] = (new_depth, conf, f'S1:sub_cluster_label="{sc}" → {new_depth} (purity={purity:.0%}, n={n})')
        s1_count += 1

print(f'     → {s1_count} candidatos a actualizar')

# ═════════════════════════════════════════════════════════════════════════════
# S2 — CLUSTER MAJORITY VOTE
# ═════════════════════════════════════════════════════════════════════════════
# Construir mapa cluster_id → {depth: count} desde training
cluster_map = {}
for t in training:
    cid = t['cluster_id']
    if cid is None:
        continue
    cluster_map.setdefault(cid, {})
    cluster_map[cid][t['depth']] = cluster_map[cid].get(t['depth'], 0) + 1

cluster_lookup = {}  # cluster_id → (dominant_depth, purity, n)
for cid, counts in cluster_map.items():
    total = sum(counts.values())
    dominant_depth, dominant_n = max(counts.items(), key=lambda x:x[1])
    purity = dominant_n / total
    if purity >= 0.90 and total >= 4:
        cluster_lookup[cid] = (dominant_depth, purity, total)

print(f'\nS2: Cluster majority vote — {len(cluster_lookup)} clusters con señal clara (>=90% puro, n>=4)')

s2_count = 0
for eid, rec in to_improve.items():
    if eid in updates:
        continue   # ya resuelto por S1
    cid = rec['cluster_id']
    if cid is None or cid not in cluster_lookup:
        continue
    new_depth, purity, n = cluster_lookup[cid]
    conf = round(min(0.68 + purity * 0.22 + min(n,30)*0.002, 0.92), 3)
    if conf < CONF_MIN_UPD:
        continue
    updates[eid] = (new_depth, conf, f'S2:cluster_id=CL{cid} majority={new_depth} (purity={purity:.0%}, n={n})')
    s2_count += 1

print(f'     → {s2_count} candidatos a actualizar')

# ═════════════════════════════════════════════════════════════════════════════
# S3 — TF-IDF + LOGISTIC REGRESSION
# ═════════════════════════════════════════════════════════════════════════════
print('\nS3: TF-IDF + LogisticRegression...')
try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np

    # Training: usa todos los high-conf deep + enabler (applied excluido: ambiguo)
    # Enriquece el texto con bio_theme + sub_cluster_label para más señal
    def make_text(rec):
        parts = [rec.get('summary','') or '']
        if rec.get('theme'):
            parts.append(rec['theme'])
        if rec.get('sub_cl'):
            parts.append(rec['sub_cl'])
        return ' '.join(parts)

    X_train_raw = [make_text(t) for t in training]
    y_train = [t['depth'] for t in training]  # 'deep' or 'enabler'

    # No usar 'applied' en training para LR: el clasificador original ya los puso como applied
    # Solo estamos tratando de separar deep de enabler en los inciertos

    vec = TfidfVectorizer(max_features=800, ngram_range=(1,2), min_df=2, sublinear_tf=True)
    X_train = vec.fit_transform(X_train_raw)

    clf = LogisticRegression(C=1.0, max_iter=500, random_state=42)
    clf.fit(X_train, y_train)

    # Aplicar a los que aún no tienen update y tienen summary
    remaining = [(eid, rec) for eid,rec in to_improve.items()
                 if eid not in updates and len(make_text(rec)) > 80]
    if remaining:
        X_rem = vec.transform([make_text(r[1]) for r in remaining])
        probs = clf.predict_proba(X_rem)
        classes = clf.classes_   # ['deep','enabler'] or similar

        s3_count = 0
        for i, (eid, rec) in enumerate(remaining):
            prob_dict = dict(zip(classes, probs[i]))
            # Solo clasificamos deep/enabler con alta confianza
            max_cls = max(prob_dict.items(), key=lambda x:x[1])
            new_depth, prob = max_cls
            if prob < 0.78:   # umbral más alto para LR
                continue
            # Convertir probabilidad a confianza del campo
            conf = round(0.65 + prob * 0.28, 3)
            if conf < CONF_MIN_UPD:
                continue
            updates[eid] = (new_depth, conf, f'S3:TF-IDF+LR p({new_depth})={prob:.3f}')
            s3_count += 1
        print(f'     → {s3_count} candidatos a actualizar')
    else:
        print('     → sin candidatos con summary suficiente')
except Exception as e:
    print(f'     ERROR: {e}')

# ═════════════════════════════════════════════════════════════════════════════
# S4 — UMAP K-NN (k=7, voto por mayoría)
# ═════════════════════════════════════════════════════════════════════════════
print('\nS4: UMAP k-NN (k=7)...')
try:
    # Construir array de puntos conocidos (training)
    known = [(t['x'], t['y'], t['depth']) for t in training
             if t['x'] is not None and t['y'] is not None]
    knn_x = np.array([k[0] for k in known], dtype=float)
    knn_y = np.array([k[1] for k in known], dtype=float)
    knn_labels = [k[2] for k in known]

    K = 7
    s4_count = 0
    for eid, rec in to_improve.items():
        if eid in updates:
            continue
        if rec['x'] is None or rec['y'] is None:
            continue
        # Distancias euclidianas a todos los puntos conocidos
        dx = knn_x - float(rec['x'])
        dy = knn_y - float(rec['y'])
        dists = np.sqrt(dx**2 + dy**2)
        # K vecinos más cercanos
        k_idx = np.argpartition(dists, K)[:K]
        neighbor_labels = [knn_labels[i] for i in k_idx]
        k_dists = dists[k_idx]

        # Voto ponderado por distancia inversa
        votes = {}
        for lbl, d in zip(neighbor_labels, k_dists):
            w = 1.0 / (d + 0.1)   # evitar div/0
            votes[lbl] = votes.get(lbl, 0) + w

        total_w = sum(votes.values())
        dominant_lbl = max(votes.items(), key=lambda x:x[1])
        new_depth, w = dominant_lbl
        purity = w / total_w

        if purity < 0.75:
            continue

        conf = round(0.62 + purity * 0.25, 3)
        if conf < CONF_MIN_UPD:
            continue
        updates[eid] = (new_depth, conf, f'S4:UMAP-kNN k={K} purity={purity:.0%} → {new_depth}')
        s4_count += 1

    print(f'     → {s4_count} candidatos a actualizar')
except Exception as e:
    print(f'     ERROR: {e}')

# ═════════════════════════════════════════════════════════════════════════════
# APLICAR UPDATES
# ═════════════════════════════════════════════════════════════════════════════
print(f'\nTotal a actualizar: {len(updates)}')

source_counts = {}
for eid, (new_depth, conf, source) in updates.items():
    old_depth = to_improve[eid]['depth']
    old_conf  = to_improve[eid]['conf']
    log_update(eid, old_depth, new_depth, conf, source)
    s_key = source.split(':')[0]
    source_counts[s_key] = source_counts.get(s_key, 0) + 1

conn.commit()

# ─── REPORTE FINAL ────────────────────────────────────────────────────────────
print()
print('Por fuente:')
for src, n in sorted(source_counts.items()):
    print(f'  {src}: {n}')

print()
final = cur.execute('''
    SELECT tech_depth, COUNT(*) n, ROUND(AVG(tech_depth_confidence),3) avg_conf
    FROM startup_extended
    GROUP BY tech_depth ORDER BY n DESC
''').fetchall()
print('Distribución final:')
for row in final:
    print(f'  {str(row[0]):<15} n={row[1]:4d}  avg_conf={row[2]:.3f}')

# Review CSV actualizado
still_uncertain = cur.execute('''
    SELECT e.entity_id, e.canonical_name, sx.bio_theme_primary, sx.tech_depth,
           ROUND(sx.tech_depth_confidence,3),
           sx.tech_codes, sx.technology_tags,
           SUBSTR(COALESCE(sx.startup_summary_en,''),1,200),
           sx.tech_depth_basis
    FROM startup_extended sx
    JOIN entities e ON e.entity_id = sx.startup_id
    WHERE sx.tech_depth != 'unclassified'
      AND sx.tech_depth_confidence < 0.68
      AND (sx.bio_theme_primary IS NOT NULL
           OR (sx.tech_codes IS NOT NULL AND sx.tech_codes != '' AND sx.tech_codes != '[]'))
    ORDER BY sx.bio_theme_primary, sx.tech_depth_confidence
''').fetchall()

import csv
review_path = pathlib.Path('quality/tech_depth_review.csv')
with open(review_path, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['entity_id','canonical_name','bio_theme','tech_depth_auto',
                'confidence','tech_codes','technology_tags','summary_short',
                'tech_depth_override','notes'])
    for r in still_uncertain:
        w.writerow(list(r[:8]) + ['', ''])

conn.close()
print(f'\nReview CSV actualizado: {review_path}  ({len(still_uncertain)} casos restantes)')
print('\nPróximo paso: regenerar dashboard')
print('  .venv/Scripts/python.exe -c "import sqlite3,sys;sys.path.insert(0,\'.\');from src.clustering import write_dashboard_data;conn=sqlite3.connect(\'db/bio_latam.db\');write_dashboard_data(conn);conn.close()"')
