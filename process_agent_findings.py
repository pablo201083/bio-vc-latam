"""
Procesa los resultados de investigación de agentes y crea edges reales
basados en fuentes verificadas (LinkedIn, prensa, directorios públicos)
"""

import sqlite3
import csv
from difflib import SequenceMatcher

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

# Cargar startup_ids
c.execute('SELECT startup_id FROM startup_extended')
startup_ids = set(row[0] for row in c.fetchall())

def fuzzy_match(name, candidates, threshold=0.65):
    best_match = None
    best_score = threshold
    for candidate in candidates:
        score = SequenceMatcher(None, name.lower(), candidate.lower()).ratio()
        if score > best_score:
            best_score = score
            best_match = candidate
    return best_match, best_score

print("=" * 80)
print("PROCESANDO RESULTADOS DE INVESTIGACION DE AGENTES")
print("=" * 80)

# MONASHEES PORTFOLIO (de agent research)
monashees_portfolio = [
    ('Sami Saúde', 'BR', 'Healthcare'),
    ('Pipo Saúde', 'BR', 'Healthtech'),
    ('Vambe', 'CL', 'Healthcare'),
    ('Rivio', 'BR', 'Healthcare'),
    ('Hilab', 'BR', 'Diagnostics'),
    ('Luzia', 'BR', 'Health'),
    ('Neon', 'BR', 'Fintech'),
    ('Creditas', 'BR', 'Fintech'),
    ('Ualá', 'AR', 'Fintech'),
    ('Clara', 'MX', 'Tech'),
]

# BIOMINAS BRASIL PORTFOLIO (de agent research)
biominas_portfolio = [
    ('Onkos', 'BR', 'Clinical/Biotech'),
    ('ImunoTera', 'BR', 'Immunotherapy'),
    ('Salutho', 'BR', 'HealthTech'),
    ('Microbiota Agrícola', 'BR', 'Ag Biologicals'),
    ('BioDiverso Insumos', 'BR', 'Ag Biologicals'),
    ('Vyro Bio', 'BR', 'Therapeutics'),
    ('Tismoo', 'BR', 'Diagnostics'),
    ('Alecrim Biotech', 'BR', 'Food Biotech'),
    ('Symbiomics', 'BR', 'Bioinputs'),
    ('InEdita Bio', 'BR', 'Gene-Edited Crops'),
    ('NemaControl Biológicos', 'BR', 'Biocontrol'),
    ('Peptidus Biotech', 'BR', 'Animal Health'),
    ('Brain4care', 'BR', 'Medical Devices'),
    ('Cellmeat Brasil', 'BR', 'Cultivated Meat'),
]

edges = []
total_matches = 0

print("\n1. MONASHEES PORTFOLIO")
print("-" * 80)

for company_name, country, sector in monashees_portfolio:
    startup_id, score = fuzzy_match(company_name, startup_ids, 0.65)

    if startup_id and score > 0.7:
        edges.append({
            'investment_id': f'AGENT_MONASHEES_{startup_id}',
            'investor_id': 'monashees',
            'startup_id': startup_id,
            'confidence_score': score,
            'source': 'agent_research: LinkedIn/Press/LAVCA'
        })
        print(f"  [OK] {company_name:30} -> {startup_id:30} ({score:.2f})")
        total_matches += 1
    else:
        print(f"  [NO MATCH] {company_name:30} (best: {startup_id if startup_id else 'none'})")

print(f"\n  Matched: {total_matches}/{len(monashees_portfolio)}")

print("\n2. BIOMINAS BRASIL PORTFOLIO")
print("-" * 80)

biominas_matched = 0

for company_name, country, sector in biominas_portfolio:
    startup_id, score = fuzzy_match(company_name, startup_ids, 0.65)

    if startup_id and score > 0.7:
        edges.append({
            'investment_id': f'AGENT_BIOMINAS_{startup_id}',
            'investor_id': 'biominas',
            'startup_id': startup_id,
            'confidence_score': score,
            'source': 'agent_research: Directory/Portfolio'
        })
        print(f"  [OK] {company_name:30} -> {startup_id:30} ({score:.2f})")
        biominas_matched += 1
    else:
        print(f"  [NO MATCH] {company_name:30}")

print(f"\n  Matched: {biominas_matched}/{len(biominas_portfolio)}")

print("\n" + "=" * 80)
print(f"RESUMEN TOTAL: {len(edges)} edges de investigación de agentes")
print("=" * 80)

# Deduplicar (en caso de overlaps)
seen = set()
unique_edges = []

for edge in edges:
    key = (edge['investor_id'], edge['startup_id'])
    if key not in seen:
        unique_edges.append(edge)
        seen.add(key)

print(f"Después de deduplicación: {len(unique_edges)} edges únicos")

# Guardar
if unique_edges:
    output_path = 'staging/agent_research_edges.csv'
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['investment_id', 'investor_id', 'startup_id', 'confidence_score', 'source'])
        writer.writeheader()
        writer.writerows(unique_edges)

    print(f"\n[OK] Guardado en {output_path}")

    # Ingeirir inmediatamente
    print("\n3. INGIRIENDO A BASE DE DATOS...")
    print("-" * 80)

    ingested = 0
    for edge in unique_edges:
        try:
            c.execute('''
            INSERT OR IGNORE INTO investment_edges (
                investment_id, investor_id, startup_id, round_name, round_stage,
                announced_date, amount, currency, is_lead, confidence_score,
                source_id, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                edge['investment_id'],
                edge['investor_id'],
                edge['startup_id'],
                'portfolio',
                None,
                None,
                None,
                None,
                0,
                edge['confidence_score'],
                'AGENT_RESEARCH',
                edge['source']
            ))
            ingested += 1
        except Exception as e:
            print(f"  Error: {e}")

    conn.commit()
    print(f"  [OK] {ingested} edges ingiridos")

# Verificar cobertura final
c.execute('''
SELECT COUNT(DISTINCT startup_id)
FROM investment_edges
WHERE startup_id IN (
  SELECT startup_id FROM startup_extended WHERE cluster_id >= 0
)
''')
covered = c.fetchone()[0]

c.execute('SELECT COUNT(*) FROM investment_edges')
total = c.fetchone()[0]

print(f"\n4. ESTADO FINAL")
print("=" * 80)
print(f"  Total edges en DB: {total}")
print(f"  Startups clustered con edges: {covered}/606 ({100*covered//606}%)")

conn.close()

print("\n[DONE]")
