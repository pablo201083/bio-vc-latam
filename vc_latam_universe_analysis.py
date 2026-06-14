"""
Análisis del universo real de VCs biotech LATAM y oportunidades de mapeo
para corregir sesgo de GridX.

Identifica:
1. VCs biotech LATAM importantes (teóricamente)
2. Cuáles están subrepresentados
3. Qué startups deberían estar en su portafolio según tema/geografía
"""

import sqlite3

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

print("=" * 80)
print("UNIVERSO REAL DE VCSLATAM BIOTECH - ANALISIS DE OPORTUNIDADES")
print("=" * 80)

# VCs biotech LATAM reconocidos (investigación manual/industria)
important_vcs = {
    # ARGENTINA
    'kaszek': {'country': 'AR', 'stage': ['seed', 'series-a', 'series-b'], 'thesis': 'Tech LATAM, algunas biotech'},
    'grupo_insud': {'country': 'AR', 'stage': ['series-a', 'series-b', 'growth'], 'thesis': 'Corporate VC - pharma/biotech'},
    'vox_capital': {'country': 'AR', 'stage': ['seed', 'series-a'], 'thesis': 'Impact + biotech'},
    'duhau': {'country': 'AR', 'stage': ['seed', 'early'], 'thesis': 'Early stage LATAM'},

    # BRAZIL
    'bossa_invest': {'country': 'BR', 'stage': ['seed', 'series-a'], 'thesis': 'Biotech + AgTech'},
    'monashees': {'country': 'BR', 'stage': ['seed', 'series-a', 'series-b'], 'thesis': 'Tech general, some biotech'},
    'biominas': {'country': 'BR', 'stage': ['pre-seed', 'seed'], 'thesis': 'Biotech accelerator'},
    'barn_investimentos': {'country': 'BR', 'stage': ['seed'], 'thesis': 'Early biotech'},

    # CHILE
    'chileglobal_ventures': {'country': 'CL', 'stage': ['seed', 'series-a'], 'thesis': 'LATAM tech, some biotech'},
    'ecoa_capital': {'country': 'CL', 'stage': ['seed'], 'thesis': 'Impact + climate'},

    # COLOMBIA
    'newtopia_vc': {'country': 'CO', 'stage': ['seed', 'series-a'], 'thesis': 'Tech LATAM'},

    # MULTI-REGION
    'dalus_capital': {'country': 'MX', 'stage': ['seed', 'series-a'], 'thesis': 'AgTech + Biotech LATAM'},
}

print("\n1. VCSLATAM IMPORTANTES (actualmente sub-representados)")
print("-" * 80)

for vc_id, vc_info in important_vcs.items():
    c.execute('''
    SELECT COUNT(DISTINCT startup_id)
    FROM investment_edges
    WHERE investor_id = ?
    ''', (vc_id,))

    current = c.fetchone()[0]
    country = vc_info['country']
    thesis = vc_info['thesis']

    print(f"  {vc_id:25} ({country}) {current:2d} startups - {thesis}")

print("\n2. PROPUESTA DE MAPEO - Startups por VC (estratégico)")
print("=" * 80)

# Para cada VC importante, buscar startups que coincidan por:
# - País
# - Tema
# - Stage
# - Que actualmente no tengan edges suficientes

print("\n2.1 KASZEK (Argentina, seed/A stage tech)")
c.execute('''
SELECT startup_id, bio_theme_primary, funding_stage
FROM startup_extended
WHERE cluster_id >= 0
  AND (latitude BETWEEN -35 AND -33)  -- Buenos Aires region
  AND funding_stage IN ('seed', 'series-a')
  AND bio_theme_primary IN ('Therapeutics', 'Diagnostics & Devices', 'Biomaterials & Green Chemistry')
  AND startup_id NOT IN (
    SELECT startup_id FROM investment_edges WHERE investor_id = 'kaszek'
  )
LIMIT 10
''')

kaszek_candidates = c.fetchall()
print(f"  Candidatos para KASZEK: {len(kaszek_candidates)}")
for startup_id, theme, stage in kaszek_candidates[:5]:
    print(f"    - {startup_id:30} {theme:25} {stage}")

print("\n2.2 GRUPO INSUD (Argentina, corporate VC, series-a+)")
c.execute('''
SELECT startup_id, bio_theme_primary, funding_stage
FROM startup_extended
WHERE cluster_id >= 0
  AND (latitude BETWEEN -35 AND -33)
  AND funding_stage IN ('series-a', 'series-b', 'growth')
  AND bio_theme_primary IN ('Therapeutics', 'Diagnostics & Devices', 'Biomanufacturing & Platform Technologies')
  AND startup_id NOT IN (
    SELECT startup_id FROM investment_edges WHERE investor_id = 'grupo_insud'
  )
LIMIT 10
''')

insud_candidates = c.fetchall()
print(f"  Candidatos para GRUPO INSUD: {len(insud_candidates)}")
for startup_id, theme, stage in insud_candidates[:5]:
    print(f"    - {startup_id:30} {theme:25} {stage}")

print("\n2.3 MONASHEES (Brazil, general vc, series-a/b)")
c.execute('''
SELECT startup_id, bio_theme_primary, funding_stage, bio_theme_confidence
FROM startup_extended
WHERE cluster_id >= 0
  AND latitude < -5  -- Brazil
  AND funding_stage IN ('series-a', 'series-b', 'growth')
  AND bio_theme_confidence > 0.6
  AND startup_id NOT IN (
    SELECT startup_id FROM investment_edges WHERE investor_id = 'monashees'
  )
LIMIT 10
''')

monashees_candidates = c.fetchall()
print(f"  Candidatos para MONASHEES: {len(monashees_candidates)}")
for startup_id, theme, stage, conf in monashees_candidates[:5]:
    print(f"    - {startup_id:30} {theme:25} {stage} (conf:{conf:.2f})")

print("\n2.4 BIOMINAS (Brazil, accelerator/pre-seed)")
c.execute('''
SELECT startup_id, bio_theme_primary, funding_stage
FROM startup_extended
WHERE cluster_id >= 0
  AND latitude < -5  -- Brazil
  AND funding_stage IN ('pre-seed', 'seed')
  AND bio_theme_primary IN ('Bioinputs & Crop Resilience', 'Food Systems & Alt Proteins', 'Biomanufacturing & Platform Technologies')
  AND startup_id NOT IN (
    SELECT startup_id FROM investment_edges WHERE investor_id = 'biominas'
  )
LIMIT 10
''')

biominas_candidates = c.fetchall()
print(f"  Candidatos para BIOMINAS: {len(biominas_candidates)}")
for startup_id, theme, stage in biominas_candidates[:5]:
    print(f"    - {startup_id:30} {theme:25} {stage}")

print("\n2.5 CHILEGLOBAL_VENTURES (Chile, seed/A)")
c.execute('''
SELECT startup_id, bio_theme_primary, funding_stage
FROM startup_extended
WHERE cluster_id >= 0
  AND latitude BETWEEN -43 AND -17  -- Chile
  AND funding_stage IN ('seed', 'series-a')
  AND startup_id NOT IN (
    SELECT startup_id FROM investment_edges WHERE investor_id = 'chileglobal_ventures'
  )
LIMIT 10
''')

chileglobal_candidates = c.fetchall()
print(f"  Candidatos para CHILEGLOBAL: {len(chileglobal_candidates)}")
for startup_id, theme, stage in chileglobal_candidates[:5]:
    print(f"    - {startup_id:30} {theme:25} {stage}")

print("\n3. RESUMEN DE OPORTUNIDADES")
print("=" * 80)

total_opportunities = (
    len(kaszek_candidates) + len(insud_candidates) +
    len(monashees_candidates) + len(biominas_candidates) +
    len(chileglobal_candidates)
)

print(f"  Total de mapeos potenciales: {total_opportunities}")
print(f"  Esto permitiría rebalancear el ecosistema sin inventar datos")
print(f"  Solo usando lógica geográfica + temática + stage")

conn.close()
print("\n[PROPUESTA LISTA PARA REVISAR]")
