"""
classify_biotheme.py
---------------------
Clasifica bio_theme_primary para empresas con scope_decision != 'include'
usando TF-IDF + LogisticRegression entrenado sobre las 490 empresas incluidas.

Dos decisiones simultáneas:
  1. ¿Es bio?       — max_prob >= umbral → candidata a inclusión
  2. ¿Qué tema?     — la clase con mayor probabilidad

Umbrales (conservadores, para no sobre-incluir):
  max_prob >= 0.72  → recomendada para include con alta confianza
  max_prob 0.50-0.72 → revisar (candidata, baja confianza)
  max_prob < 0.50   → probablemente no-bio, mantener excluida

Genera:
  quality/biotheme_candidates.csv — para revisión y aprobación del curador

NO cambia scope_decision directamente — eso lo hace el curador o un paso manual.
Sí actualiza bio_theme_primary para las recomendadas con alta confianza.

Ejecutar:
  .venv/Scripts/python.exe classify_biotheme.py
"""

import sqlite3, pathlib, datetime, sys, json, csv, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
import numpy as np

db   = pathlib.Path('db/bio_latam.db')
conn = sqlite3.connect(db)
cur  = conn.cursor()
now  = datetime.datetime.now(datetime.UTC).isoformat()

# ─── Construir texto de entrada ───────────────────────────────────────────────
# Concatena todos los campos de texto disponibles en un string rico
def make_text(summ_en, summ_v1, tech_tags, tech_codes_raw):
    parts = []
    # Preferir startup_summary_en si existe y es larga
    s = (summ_en or summ_v1 or '').strip()
    # Limpiar notas de curador como "Queda afuera por no ser..."
    s = re.sub(r'\(?[Qq]ueda (afuera|fuera)[^.]*\.?\)?', '', s).strip()
    s = re.sub(r'\(?[Ii]t is (excluded|bio-relevant)[^.]*\.?\)?', '', s).strip()
    s = re.sub(r'\(?[Nn]ot biotech[^.]*\.?\)?', '', s).strip()
    if s:
        parts.append(s)
    if tech_tags:
        parts.append(tech_tags)
    if tech_codes_raw and tech_codes_raw not in ('[]', ''):
        try:
            codes = json.loads(tech_codes_raw)
            parts.append(' '.join(codes))
        except Exception:
            pass
    return ' '.join(parts)

# ─── Cargar training set (scope=include, bio_theme conocido) ─────────────────
print('=== classify_biotheme.py ===\n')

train_rows = cur.execute('''
    SELECT sx.startup_id, sx.bio_theme_primary,
           sx.startup_summary_en, sx.startup_summary_v1,
           sx.technology_tags, sx.tech_codes
    FROM startup_extended sx
    WHERE sx.scope_decision = 'include' AND sx.bio_theme_primary IS NOT NULL
''').fetchall()

X_train_raw = [make_text(r[2], r[3], r[4], r[5]) for r in train_rows]
y_train_raw  = [r[1] for r in train_rows]

print(f'Training: {len(train_rows)} empresas, {len(set(y_train_raw))} clases')
from collections import Counter
for theme, n in Counter(y_train_raw).most_common():
    print(f'  {theme[:45]:<47} n={n}')

# ─── Entrenar modelo ──────────────────────────────────────────────────────────
vec = TfidfVectorizer(
    max_features=1200,
    ngram_range=(1, 3),
    min_df=2,
    sublinear_tf=True,
    strip_accents='unicode',
)
X_train = vec.fit_transform(X_train_raw)

le = LabelEncoder()
y_train = le.fit_transform(y_train_raw)

clf = LogisticRegression(
    C=2.0,
    max_iter=1000,
    random_state=42,
    class_weight='balanced',   # compensa las clases pequeñas (Biomanufacturing n=21)
)
clf.fit(X_train, y_train)

# Cross-val rápido para estimar accuracy
from sklearn.model_selection import cross_val_score
scores = cross_val_score(clf, X_train, y_train, cv=5, scoring='accuracy')
print(f'\nCV accuracy (5-fold): {scores.mean():.3f} ± {scores.std():.3f}')

# ─── Cargar candidatos (scope != include) ────────────────────────────────────
cand_rows = cur.execute('''
    SELECT e.entity_id, e.canonical_name, e.country_code,
           sx.scope_decision, sx.scope_status,
           sx.startup_summary_en, sx.startup_summary_v1,
           sx.technology_tags, sx.tech_codes,
           sx.bio_theme_primary
    FROM startup_extended sx JOIN entities e ON e.entity_id = sx.startup_id
    WHERE sx.scope_decision IN ('exclude', 'review')
      AND sx.bio_theme_primary IS NULL
''').fetchall()

print(f'\nCandidatos a clasificar: {len(cand_rows)}')

# ─── Predecir ────────────────────────────────────────────────────────────────
X_cand_raw = [make_text(r[5], r[6], r[7], r[8]) for r in cand_rows]
X_cand     = vec.transform(X_cand_raw)
probs      = clf.predict_proba(X_cand)      # shape (n, 8)
classes    = le.classes_

CONF_HIGH  = 0.72   # incluir automáticamente como candidata fuerte
CONF_LOW   = 0.45   # por debajo = probablemente no-bio

results = []
for i, r in enumerate(cand_rows):
    eid, name, country, scope_dec, scope_st = r[0], r[1], r[2], r[3], r[4]
    text_len = len(X_cand_raw[i])

    # Clase dominante y segunda
    top2_idx  = np.argsort(probs[i])[::-1][:2]
    top_theme = classes[top2_idx[0]]
    top_conf  = float(probs[i][top2_idx[0]])
    sec_theme = classes[top2_idx[1]]
    sec_conf  = float(probs[i][top2_idx[1]])

    if text_len < 30:
        recommendation = 'sin_texto'
    elif top_conf >= CONF_HIGH:
        recommendation = 'candidata_fuerte'
    elif top_conf >= CONF_LOW:
        recommendation = 'revisar'
    else:
        recommendation = 'no_bio'

    results.append({
        'entity_id':     eid,
        'canonical_name': name,
        'country':       country or '',
        'scope_decision': scope_dec,
        'scope_status':  scope_st,
        'recommendation': recommendation,
        'top_theme':     top_theme,
        'top_conf':      round(top_conf, 3),
        'sec_theme':     sec_theme,
        'sec_conf':      round(sec_conf, 3),
        'text_len':      text_len,
        'text_preview':  X_cand_raw[i][:120],
    })

# ─── Resumen ─────────────────────────────────────────────────────────────────
print()
rec_counts = Counter(r['recommendation'] for r in results)
print('Recomendaciones:')
for rec, n in rec_counts.most_common():
    print(f'  {rec:<22}: {n}')

print('\nCandidatas fuertes (conf >= 0.72):')
for r in sorted(results, key=lambda x: -x['top_conf']):
    if r['recommendation'] == 'candidata_fuerte':
        print(f'  {r["canonical_name"][:28]:<30} [{r["country"]}]  → {r["top_theme"][:35]:<37} conf={r["top_conf"]:.3f}  ({r["scope_decision"]})')

print('\nRevisar (conf 0.45-0.72):')
for r in sorted(results, key=lambda x: -x['top_conf']):
    if r['recommendation'] == 'revisar':
        print(f'  {r["canonical_name"][:28]:<30} [{r["country"]}]  → {r["top_theme"][:30]:<32} conf={r["top_conf"]:.3f}')

# ─── Exportar CSV para curador ───────────────────────────────────────────────
out_path = pathlib.Path('quality/biotheme_candidates.csv')
out_path.parent.mkdir(exist_ok=True)

with open(out_path, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow([
        'entity_id', 'canonical_name', 'country', 'scope_decision', 'scope_status',
        'recommendation', 'top_theme', 'top_conf', 'sec_theme', 'sec_conf',
        'curator_decision',   # include / exclude / leave
        'curator_theme',      # override si el curador cambia el tema
        'text_preview',
    ])
    for r in sorted(results, key=lambda x: (-x['top_conf'], x['recommendation'])):
        w.writerow([
            r['entity_id'], r['canonical_name'], r['country'],
            r['scope_decision'], r['scope_status'],
            r['recommendation'], r['top_theme'], r['top_conf'],
            r['sec_theme'], r['sec_conf'],
            '',  # curator_decision vacío
            '',  # curator_theme vacío
            r['text_preview'],
        ])

print(f'\n✓  CSV exportado: {out_path}  ({len(results)} filas)')

# ─── Aplicar las candidatas_fuertes sin texto sospechoso ─────────────────────
# Solo actualiza bio_theme_primary, NO cambia scope_decision
# El curador decide si incluir o no
REASON = ('auto-clasificado por TF-IDF+LR entrenado sobre 490 empresas incluidas. '
          'bio_theme_primary asignado. scope_decision NO modificado — requiere decisión del curador.')

auto_applied = 0
for r in results:
    if r['recommendation'] != 'candidata_fuerte':
        continue
    # Evitar empresas cuya descripción explicita que están excluidas
    if 'queda afuera' in r['text_preview'].lower() or 'not biotech' in r['text_preview'].lower():
        continue
    cur.execute(
        'UPDATE startup_extended SET bio_theme_primary=?, bio_theme_confidence=? WHERE startup_id=?',
        (r['top_theme'], r['top_conf'], r['entity_id']))
    cur.execute('''INSERT INTO audit_log (timestamp,actor,entity_id,table_name,field,old_value,new_value,reason)
                   VALUES (?,?,?,?,?,?,?,?)''',
                (now,'human:curador', r['entity_id'],'startup_extended','bio_theme_primary',
                 None, r['top_theme'], REASON))
    auto_applied += 1

conn.commit()
conn.close()

print(f'\nbio_theme_primary asignado a {auto_applied} empresas candidatas fuertes.')
print('scope_decision NO modificado — el curador decide cuáles incluir en el dashboard.')
print(f'\nPróximo paso:')
print(f'  1. Revisar quality/biotheme_candidates.csv')
print(f'  2. Completar "curator_decision" (include/exclude/leave) y "curator_theme" si cambiás el tema')
print(f'  3. .venv/Scripts/python.exe apply_biotheme_decisions.py')
