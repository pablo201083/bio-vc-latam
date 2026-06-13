"""
Reporte de enriquecimiento de aristas de capital.
Muestra: antes/después, distribución de confianza, impacto en el grafo.
"""

import sqlite3

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

print("=" * 80)
print("REPORTE DE ENRIQUECIMIENTO DE ARISTAS DE CAPITAL")
print("=" * 80)

# Totales actuales
c.execute('SELECT COUNT(*) FROM investment_edges')
total_edges = c.fetchone()[0]

c.execute('''
SELECT COUNT(*)
FROM investment_edges
WHERE source_id IN ('INFERRED_PATTERN', 'FALLBACK_THEME_MATCH', 'MANUAL_FINAL')
''')
new_edges = c.fetchone()[0]

original_edges = total_edges - new_edges

print(f"\n1. RESUMEN DE ARISTAS")
print("=" * 80)
print(f"  Aristas originales:  {original_edges:4d}")
print(f"  Aristas nuevas:      {new_edges:4d}")
print(f"  Total actual:        {total_edges:4d}")
print(f"  Crecimiento:         +{100*new_edges//original_edges}%")

# Desglose de nuevas aristas
print(f"\n2. DESGLOSE DE NUEVAS ARISTAS")
print("=" * 80)

c.execute('''
SELECT source_id, COUNT(*) as cnt
FROM investment_edges
WHERE source_id IN ('INFERRED_PATTERN', 'FALLBACK_THEME_MATCH', 'MANUAL_FINAL')
GROUP BY source_id
ORDER BY cnt DESC
''')

for source, count in c.fetchall():
    pct = 100 * count // new_edges
    print(f"  {source:30} {count:4d} ({pct:2d}%)")

# Distribución de confianza
print(f"\n3. DISTRIBUCION DE CONFIANZA")
print("=" * 80)

c.execute('''
SELECT
  SUM(CASE WHEN confidence_score >= 0.7 THEN 1 ELSE 0 END) as tier_alta,
  SUM(CASE WHEN confidence_score >= 0.5 AND confidence_score < 0.7 THEN 1 ELSE 0 END) as tier_media,
  SUM(CASE WHEN confidence_score >= 0.4 AND confidence_score < 0.5 THEN 1 ELSE 0 END) as tier_moderada,
  SUM(CASE WHEN confidence_score < 0.4 THEN 1 ELSE 0 END) as tier_baja
FROM investment_edges
WHERE source_id IN ('INFERRED_PATTERN', 'FALLBACK_THEME_MATCH', 'MANUAL_FINAL')
''')

alta, media, moderada, baja = c.fetchone()
print(f"  Alta (>= 0.7):                    {alta or 0:4d}")
print(f"  Media (0.5-0.7):                  {media or 0:4d}")
print(f"  Moderada (0.4-0.5):               {moderada or 0:4d}")
print(f"  Baja (< 0.4):                     {baja or 0:4d}")

# Cobertura por tema
print(f"\n4. COBERTURA POR TEMA (startups con investment_edges)")
print("=" * 80)

c.execute('''
SELECT
  s.bio_theme_primary,
  COUNT(DISTINCT s.startup_id) as total,
  COUNT(DISTINCT CASE WHEN ie.startup_id IS NOT NULL THEN s.startup_id END) as covered
FROM startup_extended s
LEFT JOIN investment_edges ie ON s.startup_id = ie.startup_id
WHERE s.cluster_id >= 0 AND s.bio_theme_primary IS NOT NULL
GROUP BY s.bio_theme_primary
ORDER BY total DESC
''')

for theme, total, covered in c.fetchall():
    pct = 100 * covered // total if total > 0 else 0
    uncovered = total - covered
    marker = "100%" if uncovered == 0 else f"{pct}%"
    print(f"  {theme:40} {covered:3d}/{total:3d} {marker:>4s}")

# Impacto en el grafo
print(f"\n5. IMPACTO EN EL GRAFO DE CAPITAL")
print("=" * 80)

c.execute('''
SELECT
  COUNT(DISTINCT investor_id) as inversores,
  COUNT(DISTINCT startup_id) as startups,
  COUNT(*) as edges
FROM investment_edges
''')

inv_count, startup_count, edge_count = c.fetchone()
print(f"  Nodos (inversores):  {inv_count}")
print(f"  Nodos (startups):    {startup_count}")
print(f"  Edges:               {edge_count}")
print(f"  Densidad promedio:   {edge_count / inv_count:.1f} edges/inversor")

# Cobertura final
c.execute('''
SELECT COUNT(DISTINCT startup_id)
FROM investment_edges
WHERE startup_id IN (
  SELECT startup_id FROM startup_extended WHERE cluster_id >= 0
)
''')
covered_clustered = c.fetchone()[0]

c.execute('SELECT COUNT(*) FROM startup_extended WHERE cluster_id >= 0')
total_clustered = c.fetchone()[0]

print(f"\n6. OBJETIVO ALCANZADO")
print("=" * 80)
print(f"  Startups clustered: {total_clustered}")
print(f"  Con investment_edges: {covered_clustered}")
print(f"  Cobertura: {100*covered_clustered//total_clustered}%")

if covered_clustered == total_clustered:
    print(f"\n  [SUCCESS] Todas las startups clustered tienen al menos 1 arista en el grafo de capital")

# Inversores más conectados (con nuevas aristas)
print(f"\n7. TOP 15 INVERSORES POR PORTFOLIO (incluye nuevas aristas)")
print("=" * 80)

c.execute('''
SELECT investor_id, COUNT(DISTINCT startup_id) as portfolio_size
FROM investment_edges
GROUP BY investor_id
ORDER BY portfolio_size DESC
LIMIT 15
''')

rank = 1
for investor_id, size in c.fetchall():
    print(f"  {rank:2d}. {investor_id:40} {size:3d} startups")
    rank += 1

print("\n[DONE]")
conn.close()
