"""
classify_tech_depth.py
-----------------------
Clasifica las 679 startups en 3 niveles de profundidad tecnológica:
  deep    — IP original, biología/química novel, ciclos R&D largos
  applied — Usa plataformas bio existentes, adapta/escala sin inventar la ciencia base
  enabler — Software, marketplace, fintech, logística que sirve al sector sin bio propia

Campos nuevos en startup_extended:
  tech_depth            TEXT  — 'deep' | 'applied' | 'enabler' | 'unclassified'
  tech_depth_confidence REAL  — 0.0–1.0
  tech_depth_basis      TEXT  — string explicando las señales usadas

Genera:
  quality/tech_depth_review.csv — empresas con confidence < 0.60, para revisión manual

Ejecutar:
  .venv/Scripts/python.exe classify_tech_depth.py
"""

import sqlite3, pathlib, datetime, sys, json, re, csv
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

db   = pathlib.Path('db/bio_latam.db')
conn = sqlite3.connect(db)
cur  = conn.cursor()
now  = datetime.datetime.now(datetime.UTC).isoformat()

REASON_PREFIX = 'rule-based tech_depth classifier v1 — '

# ─── AÑADIR COLUMNAS SI NO EXISTEN ────────────────────────────────────────────
existing = [r[1] for r in cur.execute('PRAGMA table_info(startup_extended)').fetchall()]
for col, typ in [('tech_depth', 'TEXT'), ('tech_depth_confidence', 'REAL'), ('tech_depth_basis', 'TEXT')]:
    if col not in existing:
        cur.execute(f'ALTER TABLE startup_extended ADD COLUMN {col} {typ}')
        print(f'  ✓  Columna {col} creada')

# ─── MATRICES DE SCORING ──────────────────────────────────────────────────────

# tech_codes que apuntan a deep tech (bio/chem/physics novel)
DEEP_CODES = {
    'synbio', 'nanotech', 'enzymatic', 'fermentation', 'bioinformatics',
    'formulation', 'green_chem', 'plant_breeding', 'computational_bio',
    'carbon_tech', 'clean_energy', 'water_tech',
    'therapeutics', 'diagnostics', 'biomanufacturing', 'biomaterials',
    'microbial', 'medical_devices',
}

# tech_codes que apuntan a enabler (software puro en bio)
ENABLER_CODES = {
    'saas_marketplace', 'blockchain', 'ag_finance',
}

# tech_codes ambiguos — penalización leve si son los ÚNICOS (no si combinan con deep)
DIGITAL_ONLY_CODES = {'ai_ml', 'iot', 'remote_sensing', 'robotics'}

# bio_theme → puntuación base (diferencia deep vs enabler)
THEME_SCORE = {
    'Therapeutics':                          2.5,
    'Biomanufacturing & Platform Technologies': 2.5,
    'Diagnostics & Health Access':           2.0,
    'Biomaterials & Circular Economy':       1.5,
    'Nature & Ecosystem Tech':               1.0,
    'Food Systems & Alt Proteins':           0.8,
    'Bioinputs & Crop Resilience':           0.8,
    'Farm Intelligence':                    -0.5,  # mayoría enabler
}

# Keywords en technology_tags / startup_summary_en → señales
DEEP_KW = {
    'novel', 'proprietary', 'patent', 'molecular', 'bioreactor', 'enzyme',
    'antibody', 'protein', 'rna', 'dna', 'crispr', 'genomic', 'microbiome',
    'fermentation', 'synthetic', 'discovery', 'compound', 'drug', 'therapeutic',
    'nanoparticle', 'bioactive', 'cdmo', 'gmp', 'biologic', 'biosimilar',
    'recombinant', 'culture', 'assay', 'biomarker', 'diagnostic',
}
ENABLER_KW = {
    'marketplace', 'saas', 'fintech', 'credit', 'insurance', 'logistics',
    'distribution', 'platform', 'erp', 'crm', 'subscription', 'portal',
    'agrifintech', 'rural credit', 'blockchain traceability',
}

def _parse_json_list(raw):
    if not raw:
        return []
    try:
        v = json.loads(raw)
        return v if isinstance(v, list) else []
    except Exception:
        return [t.strip() for t in re.split(r'[;,]', raw) if t.strip()]

def classify(eid, bio_theme, tech_codes_raw, tech_tags, summary):
    score = 0.0
    signals = []
    has_any_signal = False

    # 1. bio_theme base
    theme_sc = THEME_SCORE.get(bio_theme, 0.0) if bio_theme else 0.0
    if bio_theme:
        score += theme_sc
        signals.append(f'theme:{theme_sc:+.1f}({bio_theme[:20]})')
        has_any_signal = True

    # 2. tech_codes
    codes = set(_parse_json_list(tech_codes_raw))
    deep_hits = codes & DEEP_CODES
    enabler_hits = codes & ENABLER_CODES
    digital_only = codes & DIGITAL_ONLY_CODES
    bio_tech_present = bool(deep_hits)

    for c in deep_hits:
        score += 1.5
        signals.append(f'tc+:{c}')
        has_any_signal = True
    for c in enabler_hits:
        score -= 2.5
        signals.append(f'tc-:{c}')
        has_any_signal = True
    # penalizar si solo tiene digital y nada bio
    if digital_only and not bio_tech_present and not enabler_hits:
        score -= 1.0
        signals.append('digital_only:-1.0')

    # 3. keywords en technology_tags
    tags_text = (tech_tags or '').lower()
    for kw in DEEP_KW:
        if kw in tags_text:
            score += 0.5
            signals.append(f'kw+:{kw}')
            has_any_signal = True
    for kw in ENABLER_KW:
        if kw in tags_text:
            score -= 0.8
            signals.append(f'kw-:{kw}')
            has_any_signal = True

    # 4. keywords en summary (peso menor)
    summ_text = (summary or '').lower()
    deep_summ = sum(1 for kw in DEEP_KW if kw in summ_text)
    enabler_summ = sum(1 for kw in ENABLER_KW if kw in summ_text)
    if deep_summ > 0:
        inc = min(deep_summ * 0.3, 2.0)
        score += inc
        signals.append(f'summ+:{inc:.2f}(n={deep_summ})')
        has_any_signal = True
    if enabler_summ > 0:
        dec = min(enabler_summ * 0.5, 1.5)
        score -= dec
        signals.append(f'summ-:{dec:.2f}(n={enabler_summ})')
        has_any_signal = True

    # ── Clasificación (umbrales calibrados con empresas conocidas) ──
    # deep:    score >= 2.5   (Bioheuris synbio+plantbreed ≈ 4.3, Biotimize ≈ 5.5)
    # enabler: score <= -1.0  (Agrolend fintech ≈ -3.5, Agrotoken blockchain ≈ -4.5)
    # applied: en el medio
    # unclassified: sin señales en absoluto (bio_theme=NULL + sin tech_codes + sin kw)

    if not has_any_signal:
        label = 'unclassified'
        conf = 0.50
    elif score >= 2.5:
        label = 'deep'
        conf = min(0.62 + (score - 2.5) * 0.04, 0.97)
    elif score <= -1.0:
        label = 'enabler'
        conf = min(0.62 + abs(score + 1.0) * 0.05, 0.97)
    else:
        # applied — conf máxima lejos de umbrales, mínima en el centro (score≈0.75)
        label = 'applied'
        dist_to_deep    = abs(score - 2.5)
        dist_to_enabler = abs(score - (-1.0))
        min_dist = min(dist_to_deep, dist_to_enabler)
        conf = 0.52 + min_dist * 0.06
        conf = min(conf, 0.82)

    basis = REASON_PREFIX + f'score={score:.2f} → {label}  |  signals: ' + ', '.join(signals[:10])
    return label, round(conf, 3), basis, score

# ─── CLASIFICAR TODAS LAS STARTUPS ────────────────────────────────────────────
print('\n=== classify_tech_depth.py ===\n')

rows = cur.execute('''
    SELECT startup_id, bio_theme_primary, tech_codes, technology_tags, startup_summary_en
    FROM startup_extended
''').fetchall()

results = []
for eid, bio_t, tc, tt, summ in rows:
    label, conf, basis, raw_score = classify(eid, bio_t, tc, tt, summ)
    results.append((label, conf, basis, raw_score, eid))

    cur.execute('''UPDATE startup_extended
                   SET tech_depth=?, tech_depth_confidence=?, tech_depth_basis=?
                   WHERE startup_id=?''', (label, conf, basis, eid))
    cur.execute('''INSERT INTO audit_log
                     (timestamp, actor, entity_id, table_name, field, old_value, new_value, reason)
                   VALUES (?,?,?,?,?,?,?,?)''',
                (now, 'human:curador', eid, 'startup_extended', 'tech_depth',
                 None, label, basis))

conn.commit()

# ─── ESTADÍSTICAS ────────────────────────────────────────────────────────────
from collections import Counter
dist = Counter(r[0] for r in results)
low_conf = [r for r in results if r[1] < 0.60]
print(f'Distribución:')
print(f'  deep    : {dist["deep"]:4d} ({dist["deep"]/len(results)*100:.1f}%)')
print(f'  applied : {dist["applied"]:4d} ({dist["applied"]/len(results)*100:.1f}%)')
print(f'  enabler : {dist["enabler"]:4d} ({dist["enabler"]/len(results)*100:.1f}%)')
print(f'\nCasos con confidence < 0.60 (para revisión): {len(low_conf)}')

# Distribución por tema
print('\nPor bio_theme:')
theme_dist = {}
for eid, bio_t, tc, tt, summ in rows:
    t = bio_t or 'NULL'
    # find label for this eid
    pass

theme_rows = cur.execute('''
    SELECT bio_theme_primary, tech_depth, COUNT(*) n
    FROM startup_extended
    GROUP BY bio_theme_primary, tech_depth
    ORDER BY bio_theme_primary, n DESC
''').fetchall()

current_theme = None
for bio_t, depth, n in theme_rows:
    t = bio_t or 'NULL'
    if t != current_theme:
        print(f'\n  {t}:')
        current_theme = t
    print(f'    {depth:<10}: {n}')

# ─── EXPORTAR REVIEW CSV (solo casos con señales reales pero ambiguos) ────────
# Excluye: unclassified (sin señales = no hay override útil a hacer)
# Incluye: clasificados con conf < 0.68 Y que tienen bio_theme O tech_codes
review_path = pathlib.Path('quality/tech_depth_review.csv')
review_path.parent.mkdir(exist_ok=True)

review_rows = cur.execute('''
    SELECT e.entity_id, e.canonical_name, sx.bio_theme_primary, sx.tech_depth,
           ROUND(sx.tech_depth_confidence,3),
           sx.tech_codes, sx.technology_tags,
           SUBSTR(COALESCE(sx.startup_summary_en,''), 1, 200) as summary_short,
           sx.tech_depth_basis
    FROM startup_extended sx
    JOIN entities e ON e.entity_id = sx.startup_id
    WHERE sx.tech_depth != 'unclassified'
      AND sx.tech_depth_confidence < 0.68
      AND (sx.bio_theme_primary IS NOT NULL
           OR (sx.tech_codes IS NOT NULL AND sx.tech_codes != '' AND sx.tech_codes != '[]'))
    ORDER BY sx.bio_theme_primary, sx.tech_depth_confidence ASC
''').fetchall()

with open(review_path, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['entity_id','canonical_name','bio_theme','tech_depth_auto',
                'confidence','tech_codes','technology_tags','summary_short',
                'tech_depth_override','notes'])
    for r in review_rows:
        w.writerow(list(r[:8]) + ['', ''])

conn.close()
print(f'\n✓  Review CSV: {review_path}  ({len(review_rows)} filas para revisar)')
print('\nCampos añadidos:')
print('  tech_depth            — deep / applied / enabler / unclassified')
print('  tech_depth_confidence — 0.0–1.0')
print('  tech_depth_basis      — señales usadas')
print('\nPróximos pasos:')
print('  1. Abrir quality/tech_depth_review.csv en Excel')
print('  2. Completar "tech_depth_override" donde el clasificador se equivocó')
print('  3. .venv/Scripts/python.exe apply_tech_depth_overrides.py')
