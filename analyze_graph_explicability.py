"""
Análisis de explicabilidad del grafo de capital actual (1646 edges)

Métricas:
1. Sesgo de inversores (Herfindahl Index) - concentración
2. Dependencia de startups (% con 1-2 VCs vs diversificado)
3. Confianza por fuente (edad, verificabilidad)
4. Bridges (inversores que conectan temas)
5. Vacíos (qué temas tienen pocos inversores)
"""

import sqlite3
import json
from collections import defaultdict, Counter

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

print("=" * 80)
print("ANALISIS DE EXPLICABILIDAD: GRAFO DE CAPITAL (1646 edges)")
print("=" * 80)

# 1. SESGO DE INVERSORES (Herfindahl Index)
print("\n1. CONCENTRACION DE CAPITAL (Herfindahl Index)")
print("-" * 80)

c.execute('''
SELECT investor_id, COUNT(*) as portfolio_size
FROM investment_edges
WHERE startup_id IN (SELECT startup_id FROM startup_extended WHERE cluster_id >= 0)
GROUP BY investor_id
ORDER BY portfolio_size DESC
LIMIT 15
''')

investors = c.fetchall()
total_edges = sum(row[1] for row in investors)

print(f"\nTop 15 inversores por # de startups BIO financiadas:")
hh_index = 0
for inv_id, count in investors:
    pct = 100 * count / total_edges
    print(f"  {inv_id:30} {count:3d} ({pct:5.1f}%)")
    hh_index += (count / total_edges) ** 2

print(f"\nHerfindahl Index: {hh_index:.3f}")
print(f"  0.10 = mercado competitivo")
print(f"  0.25 = concentracion moderada")
print(f"  {hh_index:.3f} = {'ALTAMENTE CONCENTRADO' if hh_index > 0.25 else 'diversificado'}")

# 2. DEPENDENCIA DE STARTUPS
print("\n\n2. DEPENDENCIA DE STARTUPS (concentration of investors per startup)")
print("-" * 80)

c.execute('''
SELECT inv_count, COUNT(*) as startup_count
FROM (
  SELECT startup_id, COUNT(DISTINCT investor_id) as inv_count
  FROM investment_edges
  WHERE startup_id IN (SELECT startup_id FROM startup_extended WHERE cluster_id >= 0)
  GROUP BY startup_id
)
GROUP BY inv_count
ORDER BY inv_count DESC
''')

print(f"\nDistribution of investor diversity per startup:")
for inv_cnt, startup_cnt in c.fetchall():
    pct = 100 * startup_cnt / 383  # 383 startups with edges
    print(f"  {inv_cnt} investor(s):  {startup_cnt:3d} startups ({pct:5.1f}%)")

# Vulnerable startups (1 investor only)
c.execute('''
SELECT COUNT(*) FROM (
  SELECT startup_id, COUNT(DISTINCT investor_id) as inv_count
  FROM investment_edges
  WHERE startup_id IN (SELECT startup_id FROM startup_extended WHERE cluster_id >= 0)
  GROUP BY startup_id
  HAVING inv_count = 1
)
''')
vulnerable = c.fetchone()[0]
print(f"\nVULNERABLE: {vulnerable} startups depend on single investor (fragility risk)")

# 3. CONFIANZA POR FUENTE
print("\n\n3. CONFIANZA POR FUENTE (source distribution)")
print("-" * 80)

c.execute('''
SELECT COALESCE(source_id, '(no source)') as source_id, COUNT(*) as count, AVG(confidence_score) as avg_conf
FROM investment_edges
WHERE startup_id IN (SELECT startup_id FROM startup_extended WHERE cluster_id >= 0)
GROUP BY source_id
ORDER BY count DESC
''')

print(f"\nEdges por source (confidence score promedio):")
for source_id, count, avg_conf in c.fetchall():
    pct = 100 * count / 381
    print(f"  {source_id:35} {count:3d} ({pct:5.1f}%) | avg conf: {avg_conf:.2f}")

# 4. BRIDGES (inversores que conectan multiples temas)
print("\n\n4. BRIDGES: Inversores cross-tema")
print("-" * 80)

c.execute('''
SELECT ie.investor_id, COUNT(DISTINCT se.bio_theme_primary) as theme_count, COUNT(DISTINCT ie.startup_id) as portfolio_size
FROM investment_edges ie
JOIN startup_extended se ON ie.startup_id = se.startup_id
WHERE se.cluster_id >= 0
GROUP BY ie.investor_id
HAVING theme_count > 3
ORDER BY portfolio_size DESC
LIMIT 15
''')

print(f"\nTop 15 inversores con presencia en 4+ temas:")
for inv_id, theme_cnt, portfolio_size in c.fetchall():
    print(f"  {inv_id:30} {theme_cnt} temas × {portfolio_size} startups")

# 5. VACIOS (temas sub-representados en inversores)
print("\n\n5. VACIOS: Temas con pocos inversores")
print("-" * 80)

c.execute('''
SELECT se.bio_theme_primary, COUNT(DISTINCT ie.investor_id) as investor_count, COUNT(DISTINCT ie.startup_id) as startup_count
FROM startup_extended se
LEFT JOIN investment_edges ie ON se.startup_id = ie.startup_id
WHERE se.cluster_id >= 0
GROUP BY se.bio_theme_primary
ORDER BY investor_count ASC
''')

print(f"\nTemas por # inversores únicos (bajo = gap oportunidad):")
for theme, inv_cnt, startup_cnt in c.fetchall():
    print(f"  {theme:40} {inv_cnt:3d} inv × {startup_cnt:3d} startups")

# 6. COBERTURA POR TEMA
print("\n\n6. COBERTURA POR TEMA (% con inversores)")
print("-" * 80)

c.execute('''
SELECT
  bio_theme_primary,
  COUNT(*) as total,
  COUNT(CASE WHEN startup_id IN (SELECT DISTINCT startup_id FROM investment_edges) THEN 1 END) as with_investors
FROM startup_extended
WHERE cluster_id >= 0
GROUP BY bio_theme_primary
ORDER BY COUNT(*) DESC
''')

print(f"\nCobertura por tema:")
for theme, total, with_inv in c.fetchall():
    pct = 100 * with_inv // total if total > 0 else 0
    print(f"  {theme:40} {with_inv:3d}/{total:3d} ({pct:2d}%)")

# 7. MATRIZ INVESTOR × THEME (qué VCs especializan en qué)
print("\n\n7. ESPECIALIZACION: Top 10 inversores × tema principal")
print("-" * 80)

c.execute('''
SELECT
  ie.investor_id,
  se.bio_theme_primary,
  COUNT(*) as count
FROM investment_edges ie
JOIN startup_extended se ON ie.startup_id = se.startup_id
WHERE se.cluster_id >= 0
GROUP BY ie.investor_id, se.bio_theme_primary
ORDER BY ie.investor_id, count DESC
LIMIT 30
''')

current_inv = None
for inv_id, theme, count in c.fetchall():
    if inv_id != current_inv:
        print(f"\n{inv_id}:")
        current_inv = inv_id
    print(f"  {theme:40} {count:2d}")

print("\n\n" + "=" * 80)
print("SUMMARY: EXPLICABILITY DASHBOARD READY")
print("=" * 80)

conn.close()

print("""
NEXT STEPS FOR VISUALIZATION:
1. Herfindahl Index → show concentration warning if >0.25
2. Vulnerable startups → flag in portfolio view
3. Theme gaps → highlight low-investor themes for future rounds
4. Bridge investors → show as connectors in graph view
5. Confidence distribution → color code edges by source confidence
6. Coverage by theme → show as % bars in theme view
""")
