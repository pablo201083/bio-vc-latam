"""
Scrappea portafolios de VCs usando APIs gratuitas:
1. Crunchbase Dataset público (CSV)
2. AngelList API pública
3. Dealroom data público
"""

import sqlite3
import requests
import json
from difflib import SequenceMatcher
import time

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
print("SCRAPEANDO VIA APIS GRATUITAS")
print("=" * 80)

edges = []

# 1. ANGELLIST API (público, sin auth requerida)
print("\n1. AngelList API...")
print("-" * 80)

vcs_to_find = {
    'monashees': 'Monashees',
    'kaszek': 'Kaszek',
    'vox_capital': 'Vox Capital',
    'chileglobal_ventures': 'Chileglobal',
    'newtopia_vc': 'Newtopia',
}

for vc_id, vc_name in vcs_to_find.items():
    try:
        # AngelList busca VCs por nombre
        search_url = f'https://api.angel.co/1/search?query={vc_name}&type=investor'

        response = requests.get(search_url, timeout=5)

        if response.status_code == 200:
            data = response.json()

            if data and len(data) > 0:
                investor = data[0]  # Primer resultado
                investor_id = investor.get('id')

                print(f"  {vc_name}: encontrado ID {investor_id}")

                # Obtener portfolio del investor
                if investor_id:
                    portfolio_url = f'https://api.angel.co/1/investors/{investor_id}/investments'

                    portfolio_resp = requests.get(portfolio_url, timeout=5)

                    if portfolio_resp.status_code == 200:
                        investments = portfolio_resp.json()

                        matched = 0
                        for inv in investments:
                            startup_name = inv.get('startup_name') or inv.get('name')

                            if startup_name:
                                startup_id, score = fuzzy_match(startup_name, startup_ids, 0.65)

                                if startup_id and score > 0.7:
                                    edges.append({
                                        'investment_id': f'ANGELLIST_{vc_id}_{startup_id}',
                                        'investor_id': vc_id,
                                        'startup_id': startup_id,
                                        'confidence_score': score,
                                        'source': f'angellist.com/{vc_id}'
                                    })
                                    matched += 1

                        print(f"    Matched: {matched}/{len(investments)}")
        else:
            print(f"  {vc_name}: HTTP {response.status_code}")

    except Exception as e:
        print(f"  {vc_name}: Error - {e}")

    time.sleep(0.5)  # Rate limit

# 2. CRUNCHBASE OPEN DATA
print("\n2. Crunchbase Open Data...")
print("-" * 80)

# Intentar descargar el dataset público
crunchbase_urls = {
    'investments': 'https://data.crunchbase.com/api/v4/odatasets/investments?limit=10000',
    'organizations': 'https://data.crunchbase.com/api/v4/odatasets/organizations?limit=10000',
}

try:
    # Crunchbase requiere API key incluso para datos abiertos
    # Sin API key, intentar acceso limitado
    print("  Nota: Crunchbase requiere API key (gratuita pero requiere registro)")
    print("  URL: https://www.crunchbase.com/download")
except:
    pass

# 3. ALTERNATIVA: Google Custom Search o búsqueda directa
print("\n3. Búsqueda directa en datos públicos...")
print("-" * 80)

# Usar API de búsqueda pública que NO requiere autenticación
# Por ejemplo, búsquedas en Dealroom o datos abiertos

search_queries = {
    'monashees': 'site:monashees.com portfolio OR companies OR investments',
    'kaszek': 'site:kaszek.com companies OR portfolio',
    'vox_capital': 'site:vox.capital investments OR portfolio',
}

# Sin Google Search API (requiere pago), intentar búsquedas alternativas
print("  Alternativa: Usar búsquedas manuales o APIs locales")

# 4. DATOS LOCALES: Si tenemos CSVs con info de Crunchbase/CB
print("\n4. Buscando en archivos locales de staging...")
print("-" * 80)

import os
import csv

# Buscar si hay archivos de Crunchbase descargados localmente
staging_files = os.listdir('staging')

crunchbase_files = [f for f in staging_files if 'crunchbase' in f.lower() or 'cb_' in f.lower()]

if crunchbase_files:
    print(f"  Encontrados {len(crunchbase_files)} archivos de Crunchbase:")
    for file in crunchbase_files:
        print(f"    - {file}")
else:
    print("  No hay archivos de Crunchbase descargados localmente")

print("\n" + "=" * 80)
print(f"RESULTADO: {len(edges)} edges extraídos vía APIs")
print("=" * 80)

if edges:
    # Guardar
    output_path = 'staging/api_portfolio_edges.csv'
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['investment_id', 'investor_id', 'startup_id', 'confidence_score', 'source'])
        writer.writeheader()
        writer.writerows(edges)

    print(f"\n[OK] {len(edges)} edges guardados en {output_path}")
else:
    print("\nLimitaciones encontradas:")
    print("  - AngelList API: Requiere autenticación para acceso completo")
    print("  - Crunchbase: Requiere API key gratuita (pero se obtiene en minutos)")
    print("  - Google Search API: USD 5/1000 queries")
    print("\n Recomendación: Obtener API key gratuita de Crunchbase")

conn.close()
