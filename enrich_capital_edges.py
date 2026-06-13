"""
Enriquece las aristas de capital para las 250 startups clustered sin investment_edges.

Estrategia:
1. Identificar patrones de inversores por tema + stage + región
2. Mapear startups huérfanas a inversores afines
3. Crear aristas de inversión con confianza moderada (0.5-0.7)
"""

import sqlite3
import csv
from datetime import datetime
from collections import defaultdict

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

print("=" * 80)
print("ENRIQUECIMIENTO DE ARISTAS DE CAPITAL")
print("=" * 80)

# 1. Obtener inversores existentes y sus patrones por tema + stage
print("\n1. Analizando patrones de inversión existentes...")

c.execute('''
SELECT i.investor_id, i.investor_type, s.bio_theme_primary, s.funding_stage, COUNT(*) as count
FROM investment_edges ie
JOIN investors i ON ie.investor_id = i.investor_id
JOIN startup_extended s ON ie.startup_id = s.startup_id
WHERE s.cluster_id >= 0 AND s.bio_theme_primary IS NOT NULL
GROUP BY i.investor_id, s.bio_theme_primary, s.funding_stage
ORDER BY count DESC
''')

investor_patterns = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
for investor_id, inv_type, theme, stage, count in c.fetchall():
    investor_patterns[investor_id][(theme, stage)] = count

print(f"   Patrones analizados: {sum(len(v) for v in investor_patterns.values())} tuplas tema-stage")

# 2. Obtener startups huérfanas
print("\n2. Identificando startups sin investment_edges...")

c.execute('''
SELECT s.startup_id, s.bio_theme_primary, s.funding_stage, s.latitude, s.longitude
FROM startup_extended s
WHERE s.cluster_id >= 0 AND s.startup_id NOT IN (
  SELECT DISTINCT startup_id FROM investment_edges
)
AND s.bio_theme_primary IS NOT NULL
ORDER BY s.startup_id
''')

orphaned_startups = c.fetchall()
print(f"   Startups a enriquecer: {len(orphaned_startups)}")

# 3. Mapear inversores recomendados por tema + stage
print("\n3. Generando mapeo de inversores recomendados...")

theme_stage_investors = defaultdict(list)
c.execute('''
SELECT DISTINCT i.investor_id, s.bio_theme_primary, s.funding_stage
FROM investment_edges ie
JOIN investors i ON ie.investor_id = i.investor_id
JOIN startup_extended s ON ie.startup_id = s.startup_id
WHERE s.cluster_id >= 0
AND s.bio_theme_primary IS NOT NULL
AND s.funding_stage IS NOT NULL
''')

for investor_id, theme, stage in c.fetchall():
    if theme and stage:
        theme_stage_investors[(theme, stage)].append(investor_id)

# Eliminar duplicados
for key in theme_stage_investors:
    theme_stage_investors[key] = list(set(theme_stage_investors[key]))

print(f"   Pares tema-stage cubiertos: {len(theme_stage_investors)}")

# 4. Crear aristas propuestas
print("\n4. Creando aristas propuestas...")

proposed_edges = []
edges_created = 0

for startup_id, theme, stage, lat, lng in orphaned_startups:
    if not theme or not stage:
        continue

    # Buscar inversores para esta combinación tema-stage
    candidates = theme_stage_investors.get((theme, stage), [])

    if not candidates:
        # Fallback: buscar por tema solo
        candidates = []
        for (t, s), inv_list in theme_stage_investors.items():
            if t == theme:
                candidates.extend(inv_list)
        candidates = list(set(candidates))[:5]  # Top 5

    if not candidates:
        # Fallback: buscar por stage solo
        candidates = []
        for (t, s), inv_list in theme_stage_investors.items():
            if s == stage:
                candidates.extend(inv_list)
        candidates = list(set(candidates))[:3]  # Top 3

    # Tomar top 2 inversores (por diversidad)
    for investor_id in candidates[:2]:
        confidence = 0.5 if len(candidates) > 2 else 0.6

        proposed_edges.append({
            'investment_id': f'INFERRED_{startup_id}_{investor_id}_{len(proposed_edges)}',
            'investor_id': investor_id,
            'startup_id': startup_id,
            'round_name': stage or 'unknown',
            'round_stage': stage or 'pre-seed',
            'announced_date': None,
            'amount': None,
            'currency': None,
            'is_lead': 0,
            'confidence_score': confidence,
            'source_id': 'INFERRED_PATTERN',
            'notes': f'Inferred from {theme} + {stage} investor patterns'
        })
        edges_created += 1

print(f"   Aristas propuestas: {edges_created} para {len(orphaned_startups)} startups")

# 5. Escribir a CSV de staging
print("\n5. Escribiendo propuestas a staging...")

staging_path = 'staging/inferred_capital_edges.csv'
with open(staging_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=[
        'investment_id', 'investor_id', 'startup_id', 'round_name', 'round_stage',
        'announced_date', 'amount', 'currency', 'is_lead', 'confidence_score',
        'source_id', 'notes'
    ])
    writer.writeheader()
    for edge in proposed_edges:
        writer.writerow(edge)

print(f"   [OK] Guardado en {staging_path}")

# 6. Estadísticas
print("\n6. ESTADÍSTICAS")
print("=" * 80)

c.execute('''
SELECT s.bio_theme_primary, COUNT(DISTINCT s.startup_id) as orphaned_count
FROM startup_extended s
WHERE s.cluster_id >= 0 AND s.startup_id NOT IN (
  SELECT DISTINCT startup_id FROM investment_edges
)
AND s.bio_theme_primary IS NOT NULL
GROUP BY s.bio_theme_primary
ORDER BY orphaned_count DESC
''')

print("\nStartups huérfanas por tema:")
for theme, count in c.fetchall():
    print(f"  {theme:35} {count:3d}")

# Ver cuántas quedarían still huérfanas después de las propuestas
proposed_startup_ids = set(e['startup_id'] for e in proposed_edges)
still_orphaned = len(orphaned_startups) - len(proposed_startup_ids)

print(f"\nResumen:")
print(f"  Startups huérfanas iniciales: {len(orphaned_startups)}")
print(f"  Aristas propuestas: {edges_created}")
print(f"  Startups alcanzadas: {len(proposed_startup_ids)}")
print(f"  Aún huérfanas después: {still_orphaned}")

conn.close()

print("\n[DONE] Revisar staging/inferred_capital_edges.csv antes de ingestion.")
