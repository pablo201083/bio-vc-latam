#!/usr/bin/env python
"""Add BR VC portfolio startups to staging/discovered_startups.csv"""

import csv
from pathlib import Path

# New startups from VC portfolio sweep
new_startups = [
    ("Nintx", "BR", "therapeutics", "Drug discovery from Brazilian biodiversity. Series A $13M led by Pitanga Fund, Ecoa Capital, MOV Investimentos.", "nintx.com.br", 2011, "https://signal.nucleate.xyz/an-overview-of-brazilian-venture-captial-activity-in-biotech/", "include", 0.95, "br-03"),
    ("Autem Therapeutics", "BR", "therapeutics", "Bioelectric cancer therapy. Series A-1 $10M. FDA Breakthrough Designation for hepatocellular carcinoma.", "autemtx.com", 2017, "https://signal.nucleate.xyz/an-overview-of-brazilian-venture-captial-activity-in-biotech/", "include", 0.95, "br-03"),
    ("MiRscience Therapeutics", "BR", "therapeutics", "microRNA therapeutics for sarcopenia and cachexia. Pre-seed funded by Green Rock.", "mirscience.com.br", 2019, "https://signal.nucleate.xyz/an-overview-of-brazilian-venture-captial-activity-in-biotech/", "review", 0.8, "br-03"),
    ("Aptah Bio", "BR", "therapeutics", "RNA Widespread Correction platform. $3.8M raised via Vesper Ventures.", "aptahbio.com", 2018, "https://signal.nucleate.xyz/an-overview-of-brazilian-venture-captial-activity-in-biotech/", "review", 0.8, "br-03"),
    ("Symbiomics", "BR", "agbiotech", "Ag-biologicals from Brazilian microbiomes. Series A $15M+ led by Corteva Catalyst with Ecoa Capital, MOV, Yield Lab.", "symbiomics.com.br", 2021, "https://revistapesquisa.fapesp.br/en/deep-techs-science-based-startups-that-develop-solutions-to-complex-problems-are-gaining-focus-and-interest-in-brazil/", "include", 0.95, "br-03"),
    ("InEdita Bio", "BR", "agbiotech", "Genome-edited climate-resilient crops. Pre-seed funded by Vesper Ventures. Patent filed.", "inedita.bio", 2022, "https://www.labiotech.eu/best-biotech/biotech-startup-companies-brazil/", "include", 0.95, "br-03"),
    ("Ascribe Bio", "BR", "agbiotech", "Natural biofungicide (Phytalix). Series A $12M co-led by Acre Venture Partners & Corteva.", "ascribebio.com", 2017, "https://www.labiotech.eu/best-biotech/biotech-startup-companies-brazil/", "include", 0.9, "br-03"),
    ("Arado", "BR", "agtech", "Agribusiness marketplace connecting producers to buyers. Series A $19.5M led by Acre Venture Partners.", "arado.com.br", 2020, "https://agfundernews.com/data-dive-afns-insights-brazils-agrifoodtech-funding-grows-32-in-q1-2025-after-meagre-2024-performance", "include", 0.9, "br-03"),
]

csv_path = Path("staging/discovered_startups.csv")

# Append rows
with open(csv_path, 'a', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    for startup in new_startups:
        row = [
            startup[0],  # name
            startup[1],  # country_code
            startup[2],  # sector
            startup[3],  # description
            startup[4],  # website
            str(startup[5]) if startup[5] else "",  # founded_year
            startup[6],  # source_url
            startup[7],  # scope_recommendation
            str(startup[8]),  # confidence
            startup[9],  # batch
        ]
        writer.writerow(row)

print(f"Added {len(new_startups)} BR VC portfolio startups")
for startup in new_startups:
    print(f"  {startup[0]}")
