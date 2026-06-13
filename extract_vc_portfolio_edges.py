"""
Extrae edges reales de vc_biotech_portfolio_latam.csv
(portafolios documentados de VCs)
"""

import sqlite3
import csv
from difflib import SequenceMatcher

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

print("Extrayendo VC portfolio edges...")

# Cargar entidades
c.execute('SELECT startup_id FROM startup_extended')
startup_ids = set(row[0] for row in c.fetchall())

c.execute('SELECT investor_id FROM investors')
investor_ids = set(row[0] for row in c.fetchall())

# Editar directamente los investors conocidos (many to one mapping)
vc_mappings = {
    'SOSV': 'SOSV_IndieBio',
    'Indie Bio': 'SOSV_IndieBio',
    'Endurance Venture Capital': 'endurance_28',
    'Endurance': 'endurance_28',
    'Ara Capital': 'sp_ventures',  # Ara es parte del portafolio de SP
    'Gates Foundation': None,  # No es inversor en la DB
    'Corteva': None,  # Corporativo
    'Cazanga': None,  # No en DB
    'MOV Investimentos': None,
    'Venture Capital': None,
    'Union of Brazilian pharma labs': None,
    'BASF': None,
    'Sofinnova Partners': 'sf500',
    'Nazca': None,
    'Collaborative Fund': None,
    'Water Lemon Ventures': 'vesper_ventures',
    'Zentynel': 'zentynel',
    'ND Latam': None,
    'FEN Ventures': None,
    'YCombinator': None,
    'DILA Capital': None,
    'EDFI MC': None,
    'Meet Capital': None,
    'Alaya Capital': None,
    'Microsoft': None,
}

def find_match(name, candidates, threshold=0.65):
    best_match = None
    best_score = threshold
    for candidate in candidates:
        score = SequenceMatcher(None, name.lower(), candidate.lower()).ratio()
        if score > best_score:
            best_score = score
            best_match = candidate
    return best_match, best_score

# Process
edges = []
matched = 0

with open('staging/vc_biotech_portfolio_latam.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)

    for row in reader:
        startup_name = row['Company Name'].strip()
        source_vc = row['Source VC/Portfolio Page'].strip()

        # Extract main VC (first name before /)
        main_vc = source_vc.split('/')[0].strip()

        # Try mapping
        inv_id = None
        if main_vc in vc_mappings:
            inv_id = vc_mappings[main_vc]
        else:
            inv_id, score = find_match(main_vc, investor_ids, 0.65)

        # Find startup
        startup_id = None
        if startup_name in startup_ids:
            startup_id = startup_name
        else:
            startup_id, score = find_match(startup_name, startup_ids, 0.65)

        if inv_id and startup_id:
            edges.append({
                'investment_id': f'VC_PORTFOLIO_{main_vc}_{startup_name}'.replace(' ', '_')[:80],
                'investor_id': inv_id,
                'startup_id': startup_id,
                'round_name': 'portfolio',
                'round_stage': None,
                'announced_date': None,
                'amount': None,
                'currency': None,
                'is_lead': 0,
                'confidence_score': 0.8,
                'source_id': 'VC_BIOTECH_PORTFOLIO_LATAM',
                'notes': f'VC portfolio: {main_vc}'
            })
            matched += 1

print(f"Matched from vc_biotech_portfolio: {matched}")

# Dedup
seen = set()
unique_edges = []
for edge in edges:
    key = (edge['investor_id'], edge['startup_id'])
    if key not in seen:
        unique_edges.append(edge)
        seen.add(key)

print(f"Unique pairs: {len(unique_edges)}")

# Write
with open('staging/vc_portfolio_edges_extracted.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=[
        'investment_id', 'investor_id', 'startup_id', 'round_name', 'round_stage',
        'announced_date', 'amount', 'currency', 'is_lead', 'confidence_score',
        'source_id', 'notes'
    ])
    writer.writeheader()
    writer.writerows(unique_edges)

print(f"[OK] {len(unique_edges)} edges guardados")

conn.close()
EOF
