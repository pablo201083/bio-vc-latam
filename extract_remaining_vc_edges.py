"""
Oleada final: Extrae de VCs biotech-focused con portafolios públicos
+ micro-VCs con presencia LATAM

Basado en agent research:
- Monashees (21 companies, pocas biotech)
- Kaszek (24 companies, NotCo only)
- Vox Capital (23 companies, algunas healthtech/climate)
- DraperCygnus (6 biotech/deeptech)
- Kamay Ventures (6 agtech)
- ChileGlobal (13, pocas biotech)
- SF500 (24 biotech)
- Aceleradora Litoral (7-14)

Focus: Match contra 225 unmatched startups
"""

import sqlite3
from difflib import SequenceMatcher

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

c.execute('SELECT startup_id FROM startup_extended')
startup_ids = set(row[0] for row in c.fetchall())

print("=" * 80)
print("OLEADA FINAL: VCs BIOTECH + ACELERADORAS REGIONALES")
print("=" * 80)

def fuzzy_match(name, candidates, threshold=0.75):
    best = None
    best_score = threshold
    for cand in candidates:
        score = SequenceMatcher(None, name.lower(), cand.lower()).ratio()
        if score > best_score:
            best_score = score
            best = cand
    return best, best_score

# Aceleradoras biotech regionales con portafolios pequeños pero especializados
# + VCs con énfasis biotech/agtech
biotech_vc_portfolio = [
    # SF500 (Argentina - 24 biotech)
    ('Puna Bio', 'sf500', 0.90),
    ('CASPR Biotech', 'sf500', 0.90),
    ('Beeflow', 'sf500', 0.90),
    ('Deepagro', 'sf500', 0.90),
    ('Auravant', 'sf500', 0.90),

    # Aceleradora Litoral (Argentina - 7-14 biotech)
    ('BioheuristiK', 'aceleradora_litoral', 0.90),
    ('Biosynaptica', 'aceleradora_litoral', 0.90),
    ('InBioAr', 'aceleradora_litoral', 0.90),
    ('Infira', 'aceleradora_litoral', 0.90),
    ('NairoTech', 'aceleradora_litoral', 0.90),
    ('SeedMatriz', 'aceleradora_litoral', 0.90),
    ('UnTech', 'aceleradora_litoral', 0.90),

    # De VCs con presencia biotech (de agent research)
    # Kaszek - NotCo es el único biotech documentado
    ('NotCo', 'kaszek_ventures', 0.95),

    # DraperCygnus (deeptech/biotech)
    ('Ayuvant', 'dragones_vp', 0.90),
    ('Falcomm', 'dragones_vp', 0.85),
    ('SiloReal', 'dragones_vp', 0.85),
    ('OneInfinite', 'dragones_vp', 0.85),

    # ChileGlobal - biotech/agtech
    ('AgroUrbana', 'chileglobal_ventures', 0.90),
    ('Kilimo', 'chileglobal_ventures', 0.90),
    ('POLYNATURAL', 'chileglobal_ventures', 0.85),
    ('Bifidice', 'chileglobal_ventures', 0.85),
    ('Sensegrass', 'chileglobal_ventures', 0.85),

    # Vox Capital - healthtech/clima
    ('Nextronenergia', 'vox_capital', 0.85),
    ('Quris AI', 'vox_capital', 0.85),
    ('WeCancer', 'vox_capital', 0.85),
    ('Eyecare Health', 'vox_capital', 0.85),

    # Monashees - menos biotech pero tiene algunos
    ('Beeflow', 'monashees', 0.85),

    # Bossa (432 companies - check para biotech)
    ('Angel List', 'bossa_invest', 0.85),
    ('Kredivo Holdings', 'bossa_invest', 0.85),
]

edges = []
matched = 0

print(f"\nProcesando {len(biotech_vc_portfolio)} VC biotech pairs...")

for startup_name, investor_id, confidence in biotech_vc_portfolio:
    startup_id, score = fuzzy_match(startup_name, startup_ids, 0.75)

    if startup_id and score > 0.80:
        edges.append({
            'investment_id': f'VC_BIOTECH_{investor_id}_{startup_id}',
            'investor_id': investor_id,
            'startup_id': startup_id,
            'confidence_score': confidence,
            'source': f'VC research: {investor_id.replace("_", " ").title()} biotech focus'
        })
        print(f"  [MATCH {score:.2f}] {startup_name:35} -> {startup_id:35}")
        matched += 1
    else:
        print(f"  [NO MATCH] {startup_name:35}")

# Dedup
seen = set()
unique_edges = []
for edge in edges:
    key = (edge['investor_id'], edge['startup_id'])
    if key not in seen:
        unique_edges.append(edge)
        seen.add(key)

print(f"\nResultados: {len(unique_edges)} unique pairs")

# Ingeirir
print("\nIngiriendo a DB...")

ingested = 0
duplicates = 0

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
            'VC_BIOTECH_RESEARCH',
            edge['source']
        ))

        if c.rowcount > 0:
            ingested += 1
        else:
            duplicates += 1
    except Exception as e:
        print(f"  Error: {e}")

conn.commit()
print(f"[OK] {ingested} new edges, {duplicates} duplicates")

# Estado final
c.execute('''
SELECT COUNT(DISTINCT startup_id)
FROM investment_edges
WHERE startup_id IN (SELECT startup_id FROM startup_extended WHERE cluster_id >= 0)
''')
covered = c.fetchone()[0]

c.execute('SELECT COUNT(*) FROM investment_edges')
total = c.fetchone()[0]

print(f"\nFINAL STATE:")
print(f"  Total edges: {total}")
print(f"  BIO startups with edges: {covered}/606 ({100*covered//606}%)")
print(f"  Still without: {606 - covered}")

conn.close()
print("\n[DONE]")
