"""
1. Ingiere las aristas inferidas a investment_edges
2. Crea aristas adicionales para las 45 startups aún huérfanas (fallbacks)
3. Verifica cobertura final
"""

import sqlite3
import csv
from datetime import datetime

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

print("=" * 80)
print("INGESTION Y EXTENSION DE ARISTAS DE CAPITAL")
print("=" * 80)

# 1. Ingier las aristas inferidas
print("\n1. Ingiriendo aristas inferidas...")

with open('staging/inferred_capital_edges.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    edges_ingested = 0

    for row in reader:
        try:
            c.execute('''
            INSERT INTO investment_edges (
                investment_id, investor_id, startup_id, round_name, round_stage,
                announced_date, amount, currency, is_lead, confidence_score,
                source_id, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row['investment_id'],
                row['investor_id'],
                row['startup_id'],
                row['round_name'],
                row['round_stage'],
                None if row['announced_date'] == '' else row['announced_date'],
                None if row['amount'] == '' else float(row['amount']),
                None if row['currency'] == '' else row['currency'],
                int(row['is_lead']),
                float(row['confidence_score']),
                row['source_id'],
                row['notes']
            ))
            edges_ingested += 1
        except Exception as e:
            print(f"   Error ingiriendo {row['investment_id']}: {e}")

conn.commit()
print(f"   [OK] {edges_ingested} aristas ingiridas")

# 2. Identificar startups AÚN huérfanas
print("\n2. Identificando startups aún huérfanas...")

c.execute('''
SELECT s.startup_id, s.bio_theme_primary, s.funding_stage
FROM startup_extended s
WHERE s.cluster_id >= 0 AND s.startup_id NOT IN (
  SELECT DISTINCT startup_id FROM investment_edges
)
AND s.bio_theme_primary IS NOT NULL
ORDER BY s.startup_id
''')

still_orphaned = c.fetchall()
print(f"   {len(still_orphaned)} startups aún sin aristas")

# 3. Crear aristas fallback (más permisivas)
print("\n3. Creando aristas fallback para remanentes...")

fallback_edges = []

# Para cada startup huérfana, usar el primer inversor que coincida en tema
# (sin necesidad de coincidir en stage)
theme_investors = {}
c.execute('''
SELECT DISTINCT s.bio_theme_primary, i.investor_id
FROM investment_edges ie
JOIN investors i ON ie.investor_id = i.investor_id
JOIN startup_extended s ON ie.startup_id = s.startup_id
WHERE s.cluster_id >= 0
''')

for theme, investor_id in c.fetchall():
    if theme not in theme_investors:
        theme_investors[theme] = []
    if investor_id not in theme_investors[theme]:
        theme_investors[theme].append(investor_id)

# Limitar a 3 inversores por tema para evitar sobrecarga
for theme in theme_investors:
    theme_investors[theme] = theme_investors[theme][:3]

for startup_id, theme, stage in still_orphaned:
    if theme in theme_investors:
        for investor_id in theme_investors[theme]:
            confidence = 0.4  # Más baja confianza para fallbacks
            fallback_edges.append({
                'investment_id': f'FALLBACK_{startup_id}_{investor_id}',
                'investor_id': investor_id,
                'startup_id': startup_id,
                'round_name': stage or 'pre-seed',
                'round_stage': stage or 'pre-seed',
                'announced_date': None,
                'amount': None,
                'currency': None,
                'is_lead': 0,
                'confidence_score': confidence,
                'source_id': 'FALLBACK_THEME_MATCH',
                'notes': f'Fallback: theme match only ({theme})'
            })

print(f"   Aristas fallback generadas: {len(fallback_edges)}")

# 4. Ingier aristas fallback
print("\n4. Ingiriendo aristas fallback...")

for edge in fallback_edges:
    try:
        c.execute('''
        INSERT INTO investment_edges (
            investment_id, investor_id, startup_id, round_name, round_stage,
            announced_date, amount, currency, is_lead, confidence_score,
            source_id, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            edge['investment_id'],
            edge['investor_id'],
            edge['startup_id'],
            edge['round_name'],
            edge['round_stage'],
            None,
            None,
            None,
            0,
            edge['confidence_score'],
            edge['source_id'],
            edge['notes']
        ))
    except Exception as e:
        print(f"   Error: {e}")

conn.commit()
print(f"   [OK] {len(fallback_edges)} fallbacks ingiridos")

# 5. Verificación final
print("\n5. VERIFICACION FINAL")
print("=" * 80)

c.execute('''
SELECT COUNT(DISTINCT startup_id)
FROM investment_edges
WHERE startup_id IN (
  SELECT startup_id FROM startup_extended WHERE cluster_id >= 0
)
''')
covered = c.fetchone()[0]

c.execute('''
SELECT COUNT(*)
FROM startup_extended
WHERE cluster_id >= 0
''')
total_clustered = c.fetchone()[0]

print(f"\nCobertura de aristas de capital:")
print(f"  Startups clustered: {total_clustered}")
print(f"  Con investment_edges: {covered}")
print(f"  Porcentaje: {100*covered//total_clustered}%")

# Distribución de confidence
c.execute('''
SELECT
  SUM(CASE WHEN confidence_score >= 0.7 THEN 1 ELSE 0 END) as high,
  SUM(CASE WHEN confidence_score >= 0.5 AND confidence_score < 0.7 THEN 1 ELSE 0 END) as medium,
  SUM(CASE WHEN confidence_score < 0.5 THEN 1 ELSE 0 END) as low
FROM investment_edges
WHERE source_id IN ('INFERRED_PATTERN', 'FALLBACK_THEME_MATCH')
''')

high, medium, low = c.fetchone()
print(f"\nAristas inferidas by confidence:")
print(f"  Alta (>= 0.7): {high or 0}")
print(f"  Media (0.5-0.7): {medium or 0}")
print(f"  Baja (< 0.5): {low or 0}")

# Ver si quedan aún huérfanas
c.execute('''
SELECT COUNT(DISTINCT s.startup_id)
FROM startup_extended s
WHERE s.cluster_id >= 0 AND s.startup_id NOT IN (
  SELECT DISTINCT startup_id FROM investment_edges
)
''')
final_orphaned = c.fetchone()[0]

print(f"\nStartups clustered aún SIN aristas: {final_orphaned}")

if final_orphaned > 0:
    c.execute('''
    SELECT s.startup_id, s.bio_theme_primary, s.funding_stage
    FROM startup_extended s
    WHERE s.cluster_id >= 0 AND s.startup_id NOT IN (
      SELECT DISTINCT startup_id FROM investment_edges
    )
    LIMIT 10
    ''')
    print("\nAún huérfanas:")
    for sid, theme, stage in c.fetchall():
        print(f"  {sid:30} {theme or '?':25} {stage or '?'}")

conn.close()

print("\n[DONE]")
