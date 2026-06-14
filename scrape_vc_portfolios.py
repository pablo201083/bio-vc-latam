"""
Scrappea portafolios de VCs LATAM biotech de sus websites públicos.

Objetivos:
1. Extraer nombres de empresas de las páginas de portafolio
2. Mapear a startup_ids conocidos
3. Crear edges reales basados en data de website
"""

import sqlite3
import requests
from bs4 import BeautifulSoup
from difflib import SequenceMatcher
import time

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

# Cargar startup_ids
c.execute('SELECT startup_id FROM startup_extended')
startup_ids = set(row[0] for row in c.fetchall())

def fuzzy_match(name, candidates, threshold=0.65):
    """Busca mejor match por similaridad"""
    best_match = None
    best_score = threshold

    for candidate in candidates:
        score = SequenceMatcher(None, name.lower(), candidate.lower()).ratio()
        if score > best_score:
            best_score = score
            best_match = candidate

    return best_match, best_score

# Mapeo de fondos a URLs con portafolios
vcs_to_scrape = {
    'monashees': {
        'url': 'https://www.monashees.com/portfolio',
        'selector': '.portfolio-item, .company-card, [data-company], h3, .company-name, a[href*="companies"]',
        'name_attr': 'text'
    },
    'kaszek': {
        'url': 'https://kaszek.com/companies/',
        'selector': '.company, .portfolio-item, [class*="portfolio"], [class*="company"], h3, .card-title',
        'name_attr': 'text'
    },
    'vox_capital': {
        'url': 'https://vox.capital/en/investments/',
        'selector': '.company, .investment, [class*="portfolio"], h3, .card, a[href*="investments"]',
        'name_attr': 'text'
    },
    'chileglobal_ventures': {
        'url': 'https://chileglobalventures.cl/en/portfolio/',
        'selector': '.portfolio-company, .company-card, [class*="portfolio"], h3, .company',
        'name_attr': 'text'
    },
    'newtopia_vc': {
        'url': 'https://newtopia.vc/portfolio/',
        'selector': '.portfolio, .company, [data-company], h3, [class*="startup"], .card',
        'name_attr': 'text'
    },
}

print("=" * 80)
print("SCRAPEANDO PORTAFOLIOS DE VCS LATAM")
print("=" * 80)

extracted_edges = []

for vc_id, vc_config in vcs_to_scrape.items():
    print(f"\n[{vc_id.upper()}]")
    print(f"  URL: {vc_config['url']}")

    try:
        # Request con timeout
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(vc_config['url'], headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extraer nombres de empresas
            # Estrategia 1: Buscar en los selectores especificados
            company_names = []

            for element in soup.select(vc_config['selector']):
                # Intentar obtener el nombre
                text = element.get_text(strip=True)
                if text and len(text) > 2 and len(text) < 100:
                    company_names.append(text)

            # Estrategia 2: Si no encontró nada, buscar tags comunes
            if not company_names:
                # Buscar en href que contienen /portfolio o /companies
                for link in soup.find_all('a', href=True):
                    text = link.get_text(strip=True)
                    if text and 5 < len(text) < 80:
                        company_names.append(text)

            # Limpieza de duplicados y nombres cortos
            company_names = list(set(
                name for name in company_names
                if len(name) > 3 and name.isalpha() or ' ' in name
            ))

            print(f"  Encontrados {len(company_names)} nombres potenciales")

            # Mapear a startup_ids
            matched = 0
            for company_name in company_names[:30]:  # Limitar a 30 por VC
                startup_id, score = fuzzy_match(company_name, startup_ids, 0.60)

                if startup_id and score > 0.65:
                    extracted_edges.append({
                        'investment_id': f'WEBSITE_{vc_id}_{startup_id}',
                        'investor_id': vc_id,
                        'startup_id': startup_id,
                        'confidence_score': score,
                        'source': f'{vc_id} website portfolio'
                    })
                    matched += 1
                    print(f"    [OK] {company_name:30} -> {startup_id:30} ({score:.2f})")

            print(f"  Matched: {matched}/{len(company_names)}")

        else:
            print(f"  [HTTP {response.status_code}]")

    except requests.exceptions.Timeout:
        print(f"  [TIMEOUT] {vc_config['url']}")
    except Exception as e:
        print(f"  [ERROR] {e}")

    # Respetar rate limits
    time.sleep(1)

print("\n" + "=" * 80)
print(f"RESUMEN: {len(extracted_edges)} edges potenciales extraídos")
print("=" * 80)

# Guardar a CSV
import csv

output_path = 'staging/vc_website_portfolio_edges.csv'
with open(output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['investment_id', 'investor_id', 'startup_id', 'confidence_score', 'source'])
    writer.writeheader()
    writer.writerows(extracted_edges)

print(f"\n[OK] Guardado en {output_path}")
print(f"Listos para ingestion si confías en los matches")

conn.close()
