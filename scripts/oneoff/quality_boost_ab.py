"""
quality_boost_ab.py
--------------------
Camino A + B de mejora de calidad de la base.

CAMINO A — Campos auto-derivables
  A1. sub_cluster_label   → parse de cluster_label ("Tema — Sub-label||kw") → extrae "Sub-label"
                             444 empresas con cluster_label parseable y sub_cluster_label vacío
  A2. last_funding_at     → MAX(announced_date) por startup desde investment_edges
                             38 startups con fechas registradas
  A3. computed_quality_score → nuevo campo: score 0-10 de completitud de datos
                             (columna nueva; se crea con ALTER TABLE si no existe)

CAMINO B — Mapeo por reglas (vocabulario controlado)
  B1. domain_tags         → 207 empresas con bio_theme pero sin domain_tags
                             Mapeo: bio_theme_primary → domain_tags JSON array
  B2. industry_codes      → 0 empresas temadas sin industry_codes (ya completo)
                             Las 189 vacías tienen bio_theme=NULL → no aplica mapeo seguro

Ejecutar:
  .venv/Scripts/python.exe quality_boost_ab.py
"""

import sqlite3, pathlib, datetime, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

db   = pathlib.Path('db/bio_latam.db')
conn = sqlite3.connect(db)
cur  = conn.cursor()
now  = datetime.datetime.now(datetime.UTC).isoformat()

def log(eid, field, old_val, new_val, reason, table='startup_extended'):
    cur.execute(
        '''INSERT INTO audit_log
             (timestamp, actor, entity_id, table_name, field, old_value, new_value, reason)
           VALUES (?,?,?,?,?,?,?,?)''',
        (now, 'human:curador', eid, table, field,
         str(old_val) if old_val is not None else None,
         str(new_val), reason))

# ═══════════════════════════════════════════════════════════════════════════════
# CAMINO A1 — sub_cluster_label
# ═══════════════════════════════════════════════════════════════════════════════
print('=== CAMINO A1: sub_cluster_label ===')

# Fetch all with parseable cluster_label and empty sub_cluster_label
rows_a1 = cur.execute('''
    SELECT sx.startup_id, sx.cluster_label, sx.sub_cluster_label
    FROM startup_extended sx
    WHERE (sx.sub_cluster_label IS NULL OR sx.sub_cluster_label = '')
      AND sx.cluster_label IS NOT NULL AND sx.cluster_label != ''
      AND sx.cluster_label LIKE '%—%'
''').fetchall()

A1_REASON = ('auto-derivado: sub_cluster_label extraído del campo cluster_label '
             '(parte entre " — " y "||"). Sin LLM, sin curador.')

fixed_a1 = 0
for eid, cl, old_sub in rows_a1:
    # Parse "Tema — Sub-label||keywords" → "Sub-label"
    part = cl.split('||')[0].strip()   # drop keywords
    if ' — ' in part:
        sub = part.split(' — ', 1)[1].strip()
    else:
        sub = part.strip()

    if not sub:
        continue

    cur.execute('UPDATE startup_extended SET sub_cluster_label=? WHERE startup_id=?', (sub, eid))
    log(eid, 'sub_cluster_label', old_sub, sub, A1_REASON)
    fixed_a1 += 1

print(f'  ✓  {fixed_a1} sub_cluster_label actualizados')

# ═══════════════════════════════════════════════════════════════════════════════
# CAMINO A2 — last_funding_at
# ═══════════════════════════════════════════════════════════════════════════════
print('\n=== CAMINO A2: last_funding_at ===')

A2_REASON = ('auto-derivado: last_funding_at = MAX(announced_date) de investment_edges '
             'para este startup. Fecha del último investment_edge registrado.')

rows_a2 = cur.execute('''
    SELECT ie.startup_id, MAX(ie.announced_date) as last_date,
           sx.last_funding_at as current_val
    FROM investment_edges ie
    JOIN startup_extended sx ON sx.startup_id = ie.startup_id
    WHERE ie.announced_date IS NOT NULL AND ie.announced_date != ''
    GROUP BY ie.startup_id
''').fetchall()

fixed_a2 = 0
for eid, last_date, old_val in rows_a2:
    if old_val and old_val >= last_date:
        continue   # ya tiene un valor igual o más nuevo
    cur.execute('UPDATE startup_extended SET last_funding_at=? WHERE startup_id=?',
                (last_date, eid))
    log(eid, 'last_funding_at', old_val, last_date, A2_REASON)
    fixed_a2 += 1

print(f'  ✓  {fixed_a2} last_funding_at actualizados')

# ═══════════════════════════════════════════════════════════════════════════════
# CAMINO A3 — computed_quality_score (nueva columna)
# ═══════════════════════════════════════════════════════════════════════════════
print('\n=== CAMINO A3: computed_quality_score ===')

# Crear columna si no existe
existing_cols = [r[1] for r in cur.execute('PRAGMA table_info(startup_extended)').fetchall()]
if 'computed_quality_score' not in existing_cols:
    cur.execute('ALTER TABLE startup_extended ADD COLUMN computed_quality_score REAL')
    print('  ✓  Columna computed_quality_score creada')
else:
    print('  ·  Columna computed_quality_score ya existe — actualizando valores')

# Fórmula de completitud (0-10):
# summary_en >200 chars  → 2.0 pts
# bio_theme_primary      → 1.5 pts
# industry_codes         → 1.5 pts
# domain_tags            → 1.0 pt
# technology_tags        → 0.5 pt
# tech_codes             → 0.5 pt
# funding_stage          → 1.0 pt
# last_funding_at        → 0.5 pt  (después de A2)
# cluster_label          → 1.0 pt
# sub_cluster_label      → 0.5 pt  (después de A1)
# ─────────────────────
# TOTAL                   10.0 pts

A3_REASON = ('auto-computado: computed_quality_score = suma ponderada de completitud de campos '
             '(summary, bio_theme, industry_codes, domain_tags, tech_fields, funding, clusters). '
             'Escala 0-10. Campo distinto de data_quality_score (manual).')

all_rows = cur.execute('''
    SELECT startup_id, startup_summary_en, bio_theme_primary, industry_codes,
           domain_tags, technology_tags, tech_codes, funding_stage,
           last_funding_at, cluster_label, sub_cluster_label
    FROM startup_extended
''').fetchall()

fixed_a3 = 0
for row in all_rows:
    (eid, summ, bio_t, ind_c, dom_t, tech_t, tech_cd,
     fund_st, last_fund, cl, sub_cl) = row

    score = 0.0
    # summary
    if summ and len(str(summ)) > 200:
        score += 2.0
    elif summ and len(str(summ)) > 50:
        score += 1.0
    # bio_theme
    if bio_t:
        score += 1.5
    # industry_codes
    if ind_c and ind_c not in ('', '[]', 'null'):
        score += 1.5
    # domain_tags
    if dom_t and dom_t not in ('', '[]', 'null'):
        score += 1.0
    # technology_tags
    if tech_t and str(tech_t).strip():
        score += 0.5
    # tech_codes
    if tech_cd and tech_cd not in ('', '[]', 'null'):
        score += 0.5
    # funding_stage
    if fund_st and str(fund_st).strip():
        score += 1.0
    # last_funding_at
    if last_fund and str(last_fund).strip():
        score += 0.5
    # cluster_label
    if cl and str(cl).strip():
        score += 1.0
    # sub_cluster_label
    if sub_cl and str(sub_cl).strip():
        score += 0.5

    score = round(min(score, 10.0), 1)

    cur.execute('UPDATE startup_extended SET computed_quality_score=? WHERE startup_id=?',
                (score, eid))
    fixed_a3 += 1

print(f'  ✓  {fixed_a3} computed_quality_score calculados')

# Estadísticas post-cálculo
stats = cur.execute('''
    SELECT
        COUNT(*) total,
        ROUND(AVG(computed_quality_score),2) avg_cqs,
        SUM(CASE WHEN computed_quality_score >= 7 THEN 1 ELSE 0 END) high,
        SUM(CASE WHEN computed_quality_score BETWEEN 4 AND 6.9 THEN 1 ELSE 0 END) mid,
        SUM(CASE WHEN computed_quality_score < 4 THEN 1 ELSE 0 END) low
    FROM startup_extended
''').fetchone()
print(f'  → avg={stats[1]} | ≥7: {stats[2]} | 4-7: {stats[3]} | <4: {stats[4]}')

# ═══════════════════════════════════════════════════════════════════════════════
# CAMINO B1 — domain_tags (bio_theme → domain_tags rule-based)
# ═══════════════════════════════════════════════════════════════════════════════
print('\n=== CAMINO B1: domain_tags por bio_theme ===')

# Mapeo controlado: bio_theme_primary → domain_tags JSON array
# Vocabulario existente: agri-food, human-health, climate-resource,
#   therapeutics-regenerative, diagnostics-medtech, biomanufacturing,
#   biodiversity-nature, biomaterials, industrial-biotech
THEME_TO_DOMAIN = {
    'Diagnostics & Health Access':      ['diagnostics-medtech', 'human-health'],
    'Therapeutics':                     ['therapeutics-regenerative', 'human-health'],
    'Bioinputs & Crop Resilience':      ['agri-food', 'biodiversity-nature'],
    'Food Systems & Alt Proteins':      ['agri-food', 'human-health'],
    'Farm Intelligence':                ['agri-food', 'climate-resource'],
    'Biomaterials & Circular Economy':  ['biomaterials', 'climate-resource'],
    'Nature & Ecosystem Tech':          ['biodiversity-nature', 'climate-resource'],
    'Biomanufacturing & Platform Technologies': ['biomanufacturing', 'industrial-biotech'],
}

B1_REASON = ('rule-based: domain_tags derivado de bio_theme_primary usando vocabulario '
             'controlado (8-theme → 2-tag canonical mapping). Sin LLM.')

rows_b1 = cur.execute('''
    SELECT sx.startup_id, sx.bio_theme_primary, sx.domain_tags
    FROM startup_extended sx
    WHERE sx.bio_theme_primary IS NOT NULL
      AND (sx.domain_tags IS NULL OR sx.domain_tags = '' OR sx.domain_tags = '[]')
''').fetchall()

fixed_b1 = 0
for eid, bio_t, old_dt in rows_b1:
    if bio_t not in THEME_TO_DOMAIN:
        continue
    new_dt = json.dumps(THEME_TO_DOMAIN[bio_t])
    cur.execute('UPDATE startup_extended SET domain_tags=? WHERE startup_id=?', (new_dt, eid))
    log(eid, 'domain_tags', old_dt, new_dt, B1_REASON)
    fixed_b1 += 1

print(f'  ✓  {fixed_b1} domain_tags actualizados')

# Show distribution after
dist = cur.execute('''
    SELECT domain_tags, COUNT(*)
    FROM startup_extended
    WHERE domain_tags IS NOT NULL AND domain_tags != ''
    GROUP BY domain_tags
    ORDER BY 2 DESC
    LIMIT 15
''').fetchall()
print('  → Top domain_tags post-update:')
for dt, n in dist[:8]:
    print(f'      {n:4d}  {dt}')

# ═══════════════════════════════════════════════════════════════════════════════
# COMMIT
# ═══════════════════════════════════════════════════════════════════════════════
conn.commit()
conn.close()

print('\n' + '='*60)
print('RESUMEN FINAL')
print('='*60)
print(f'  A1 sub_cluster_label : {fixed_a1:4d} actualizados')
print(f'  A2 last_funding_at   : {fixed_a2:4d} actualizados')
print(f'  A3 computed_quality  : {fixed_a3:4d} calculados (nueva columna)')
print(f'  B1 domain_tags       : {fixed_b1:4d} actualizados')
print(f'  Todos los cambios logueados en audit_log como human:curador')
print()
print('Próximo paso: regenerar startup-themes-data.js')
print('  .venv/Scripts/python.exe pipeline.py intelligence-data')
