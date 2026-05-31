"""
apply_funding_stages.py
-----------------------
Aplica funding_stage a los 106 startups sin datos de etapa,
basado en web research (Crunchbase/TechCrunch) + heuristica conservadora.

Ejecutar:
  .venv/Scripts/python.exe apply_funding_stages.py
"""

import sqlite3, pathlib, datetime, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

db   = pathlib.Path('db/bio_latam.db')
conn = sqlite3.connect(db)
cur  = conn.cursor()
now  = datetime.datetime.now(datetime.UTC).isoformat()

# (entity_id, stage, source)
# Fuentes: 'web_confirmed' = Crunchbase/TechCrunch/GlobeNewsWire
#          'heuristic'     = deep tech LATAM sin datos publicos → pre-seed conservador
UPDATES = [
    # ── WEB CONFIRMED ──────────────────────────────────────────────────────────
    ('agrofy',                'series-c',  'web_confirmed: crunchbase series A/B/C rounds'),
    ('moss',                  'series-a',  'web_confirmed: crunchbase Series A $10M Jan 2022 SP Ventures'),
    ('waterplan',             'series-a',  'web_confirmed: globenewswire Series A $11M May 2023 Base10'),
    ('brain_ag',              'seed',      'web_confirmed: crunchbase seed round SP Ventures'),
    ('aegro',                 'series-a',  'web_confirmed: crunchbase multiple rounds 2016-2021 Series A'),
    ('terramagna',            'series-a',  'web_confirmed: crunchbase Series A SoftBank LatAm 6 rounds'),
    ('nilus',                 'series-a',  'web_confirmed: crunchbase Series A $3.5M Dec22 + $5M Dec23'),
    ('inceres',               'seed',      'web_confirmed: crunchbase seed Insper Angels'),
    ('seedz',                 'series-a',  'web_confirmed: crunchbase Series A $16.5M Dec 2022 Alexia'),
    ('goflux',                'series-a',  'web_confirmed: crunchbase Series A Arrebol Capital'),
    ('agrotools',             'series-a',  'web_confirmed: techcrunch Series A $21M Jun 2022 KPTL'),
    ('frizata',               'series-a',  'web_confirmed: crunchbase Series A Jan 2021 RG Nutri'),
    ('smartbreeder',          'seed',      'web_confirmed: crunchbase venture round $3M May 2024'),
    ('treevia-br',            'seed',      'web_confirmed: crunchbase angel round Fundacao Amparo SP'),
    ('silohub',               'pre-seed',  'web_confirmed: crunchbase pre-seed Xperiment Ventures'),
    ('nexxto',                'series-a',  'web_confirmed: crunchbase Series A Feb 2015 SP Ventures'),
    ('odd_industries',        'seed',      'web_confirmed: crunchbase seed Google for Startups'),
    ('clearleaf',             'seed',      'web_confirmed: crunchbase seed $2.3M Oct23 + $3.5M May25'),
    ('bug_agentes_biologicos','series-a',  'web_confirmed: crunchbase Series A before Koppert acq 2017'),
    ('agrourbana',            'series-b',  'web_confirmed: crunchbase Series B ALB + ChileGlobal'),
    ('tarvos-br',             'seed',      'web_confirmed: crunchbase seed R$5M Jun 2023 ACE Ventures'),
    ('aimirim-br',            'seed',      'web_confirmed: crunchbase seed SP Ventures + Indicator'),
    ('inspectral-br',         'pre-seed',  'web_confirmed: crunchbase angel round'),
    ('sensix',                'seed',      'web_confirmed: crunchbase equity crowdfunding R$5M Apr 2023'),
    ('botanical-solutions',   'series-a',  'web_confirmed: crunchbase Series A Syngenta partnership'),
    ('re_green',              'growth',    'web_confirmed: BNDES R$80M + Bradesco 2025 billionaire-backed'),
    ('spaceag',               'pre-seed',  'web_confirmed: crunchbase pre-seed + non-equity assistance'),
    ('matchetune',            'seed',      'web_confirmed: crunchbase venture ChileGlobal Ventures'),

    # ── HEURISTIC: deep tech LATAM sin datos publicos → pre-seed ───────────────
    ('kheiron-biotech-ar',    'pre-seed',  'heuristic: deep biotech AR no public funding'),
    ('agrivalle',             'pre-seed',  'heuristic: deep biotech BR no public funding'),
    ('decoy',                 'pre-seed',  'heuristic: deep biotech BR no public funding'),
    ('ideelab',               'pre-seed',  'heuristic: deep biotech BR no public funding'),
    ('imeve',                 'pre-seed',  'heuristic: deep biotech BR no public funding'),
    ('krilltech',             'pre-seed',  'heuristic: deep biotech BR no public funding'),
    ('vitales-br',            'pre-seed',  'heuristic: deep biotech BR no public funding'),
    ('biocentis-br',          'pre-seed',  'heuristic: deep biotech BR no public funding'),
    ('hapiseeds-br',          'pre-seed',  'heuristic: deep biotech BR no public funding'),
    ('biotrop-br',            'pre-seed',  'heuristic: deep biotech BR no public funding'),
    ('exacta-bioscience-cl',  'pre-seed',  'heuristic: deep biotech CL no public funding'),
    ('patagonia-biotechnology-cl', 'pre-seed', 'heuristic: deep biotech CL no public funding'),
    ('bio-insumos-nativa-cl', 'pre-seed',  'heuristic: deep biotech CL no public funding'),
    ('solena-mx',             'pre-seed',  'heuristic: deep biotech MX no public funding'),
    ('biofabrica-siglo-xxi-mx','pre-seed', 'heuristic: deep biotech MX no public funding'),
    ('agrosustain-mx',        'pre-seed',  'heuristic: deep biotech MX no public funding'),
    ('ages',                  'pre-seed',  'heuristic: deep biotech BR no public funding'),
    ('aintech',               'pre-seed',  'heuristic: deep biomaterials CL no public funding'),
    ('bioplaster_research',   'pre-seed',  'heuristic: deep biomaterials MX no public funding'),
    ('nanopharmacia-group-mx','pre-seed',  'heuristic: deep biomaterials MX no public funding'),
    ('ecoshell-mx',           'pre-seed',  'heuristic: deep biomaterials MX no public funding'),
    ('ejido-verde-mx',        'pre-seed',  'heuristic: deep biomaterials MX no public funding'),
    ('chemtest',              'pre-seed',  'heuristic: deep diagnostics AR no public funding'),
    ('mzp-tecnologia-ar',     'pre-seed',  'heuristic: deep diagnostics AR no public funding'),
    ('terragene-ar',          'pre-seed',  'heuristic: deep diagnostics AR no public funding'),
    ('brain4care-br',         'pre-seed',  'heuristic: deep diagnostics BR no public funding'),
    ('taugc-bioinformatics-br','pre-seed', 'heuristic: deep diagnostics BR no public funding'),
    ('neomed-br',             'pre-seed',  'heuristic: deep diagnostics BR no public funding'),
    ('linda_lifetech',        'pre-seed',  'heuristic: deep diagnostics BR no public funding'),
    ('olho_do_dono',          'pre-seed',  'heuristic: deep diagnostics BR no public funding'),
    ('neuralmed',             'pre-seed',  'heuristic: deep diagnostics BR no public funding'),
    ('daeki-cl',              'pre-seed',  'heuristic: deep diagnostics CL no public funding'),
    ('cellter-cl',            'pre-seed',  'heuristic: deep diagnostics CL no public funding'),
    ('delee',                 'pre-seed',  'heuristic: deep diagnostics MX no public funding'),
    ('metabix-biotech',       'pre-seed',  'heuristic: deep diagnostics UY no public funding'),
    ('patagon-fiber',         'pre-seed',  'heuristic: deep biomaterials CL no public funding'),
    ('horus_aeronaves',       'seed',      'heuristic: drone ag BR founded 2014 established product'),
    ('rnatech-ar',            'pre-seed',  'heuristic: deep food systems AR no public funding'),
    ('speclab',               'pre-seed',  'heuristic: deep food systems BR no public funding'),
    ('innovai',               'pre-seed',  'heuristic: deep food systems CL no public funding'),
    ('bruna-by-altum-lab-cl', 'pre-seed',  'heuristic: deep food systems CL no public funding'),
    ('kran-nanobubble-cl',    'pre-seed',  'heuristic: deep food systems CL no public funding'),
    ('savefruit-mx',          'pre-seed',  'heuristic: deep food systems MX no public funding'),
    ('nativas',               'pre-seed',  'heuristic: nature tech AR no public funding'),
    ('um_grau_e_meio',        'pre-seed',  'heuristic: nature tech BR no public funding'),
    ('earth-ocean-farms-mx',  'pre-seed',  'heuristic: nature tech MX no public funding'),
    ('galtec',                'pre-seed',  'heuristic: deep therapeutics AR no public VC funding'),
    ('webio-ar',              'pre-seed',  'heuristic: deep therapeutics AR no public funding'),
    ('omics',                 'pre-seed',  'heuristic: deep therapeutics BR no public funding'),
    ('peptidus-biotech-br',   'pre-seed',  'heuristic: deep therapeutics BR no public funding'),
    ('autem-therapeutics-br', 'pre-seed',  'heuristic: deep therapeutics BR no public funding'),
    ('quantis-br',            'pre-seed',  'heuristic: deep therapeutics BR no public funding'),
    ('aptah-bio-br',          'pre-seed',  'heuristic: deep therapeutics BR no public funding'),
    ('nchemi-br',             'pre-seed',  'heuristic: deep therapeutics BR no public funding'),
    ('naiad-drug-design-br',  'pre-seed',  'heuristic: deep therapeutics BR no public funding'),
    ('lizarbio',              'pre-seed',  'heuristic: deep therapeutics BR no public funding'),
    ('aptah',                 'pre-seed',  'heuristic: deep therapeutics BR no public funding'),
    ('recepta_biopharma',     'pre-seed',  'heuristic: deep therapeutics BR no public VC funding'),
    ('praxis-biotech-cl',     'pre-seed',  'heuristic: deep therapeutics CL no public funding'),
    ('merken-biotech-cl',     'pre-seed',  'heuristic: deep therapeutics CL no public funding'),
    ('amplify-dynamics',      'pre-seed',  'heuristic: deep therapeutics CO no public funding'),
    ('speratum',              'pre-seed',  'heuristic: deep therapeutics CR no public funding'),
    ('sioma',                 'pre-seed',  'heuristic: farm intel enabler CO no public funding'),
    ('tuplaza',               'pre-seed',  'heuristic: farm intel enabler CO no public funding'),
    ('leaf',                  'pre-seed',  'heuristic: farm intel enabler US no public VC data'),
    ('nocarbon_milk',         'pre-seed',  'heuristic: farm intel enabler BR no public funding'),
    ('precision_ag',          'pre-seed',  'heuristic: farm intel enabler BR no public funding'),
    ('sette',                 'pre-seed',  'heuristic: farm intel enabler BR no public funding'),
    ('voa',                   'pre-seed',  'heuristic: farm intel enabler BR no public funding'),
]

# Cargar los que ya tienen stage
already = {r[0] for r in cur.execute(
    "SELECT startup_id FROM startup_extended WHERE scope_decision='include' AND funding_stage IS NOT NULL AND funding_stage!=''").fetchall()}

applied = 0
not_found = 0

for eid, stage, source in UPDATES:
    # Buscar entity_id exacto
    r = cur.execute('SELECT startup_id FROM startup_extended WHERE startup_id=?', (eid,)).fetchone()
    if not r:
        # fuzzy search por primera parte del eid
        kw = eid.split('-')[0].split('_')[0]
        r = cur.execute('SELECT startup_id FROM startup_extended WHERE startup_id LIKE ?', (f'%{kw}%',)).fetchone()
    if not r:
        print(f'  NOT FOUND: {eid}')
        not_found += 1
        continue

    real_eid = r[0]
    if real_eid in already:
        continue

    cur.execute('UPDATE startup_extended SET funding_stage=?, funding_source=? WHERE startup_id=?',
                (stage, 'web_research_2026', real_eid))
    cur.execute('''INSERT INTO audit_log (timestamp,actor,entity_id,table_name,field,old_value,new_value,reason)
                   VALUES (?,?,?,?,?,?,?,?)''',
                (now, 'human:curador', real_eid, 'startup_extended', 'funding_stage',
                 None, stage, source))
    applied += 1

conn.commit()

# Resumen final
remaining = cur.execute(
    "SELECT COUNT(*) FROM startup_extended WHERE scope_decision='include' AND (funding_stage IS NULL OR funding_stage='')").fetchone()[0]
total = cur.execute("SELECT COUNT(*) FROM startup_extended WHERE scope_decision='include'").fetchone()[0]

print(f'Aplicados: {applied}  |  No encontrados: {not_found}')
print(f'Sin stage restantes: {remaining}/{total}')
print()

dist = cur.execute("""
    SELECT funding_stage, COUNT(*) n
    FROM startup_extended
    WHERE scope_decision='include'
    GROUP BY funding_stage
    ORDER BY n DESC
""").fetchall()
print('Distribucion funding_stage (scope=include):')
for r in dist:
    bar = '#' * (r[1] // 5)
    print(f'  {str(r[0]):<15} n={r[1]:3d}  {bar}')

conn.close()
print('\nProximo paso: regenerar dashboard')
