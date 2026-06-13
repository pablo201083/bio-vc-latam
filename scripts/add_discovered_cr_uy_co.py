#!/usr/bin/env python
"""Add discovered startups from CR, UY, CO to staging/discovered_startups.csv"""

new_startups = [
    # Costa Rica
    ("Speratum", "CR", "therapeutics", "MicroRNA-directed oncology therapies for pancreatic and ovarian cancers using proprietary miRNA technology.", "speratum.com", 2014, "https://www.lavca.org/carao-ventures-leads-us2m-follow-on-investment-in-costa-rican-biotech-startup-speratum/", "include", 0.95, "cr-01"),
    ("Green Xpo Lab", "CR", "agtech", "Remote monitoring platform for crop health assessment, deforestation prevention, and plant density verification through satellite imagery.", "greenxpolab.com", 2021, "https://contxto.com/en/costa-rica/costa-rican-startup-transforming-agriculture-through-remote-monitoring-technology/", "include", 0.85, "cr-01"),
    # Uruguay
    ("Xeptiva Therapeutics", "UY", "therapeutics", "Develops vaccines for chronic inflammatory conditions in companion animals including osteoarthritis pain and atopic dermatitis.", "xeptiva.com", 2021, "https://www.entnerd.com/en/xeptiva-therapeutics-uruguayan-scientific-start-up-raises-us-2-5-million-to-develop-veterinary-vaccines/", "include", 0.95, "uy-01"),
    ("MetaBIX Biotech", "UY", "agbiotech", "AI-powered platform for early detection of microbiological risks in livestock farms by analyzing air samples to detect pathogens.", "crunchbase.com/organization/metabix-biotech", 2022, "https://www.uruguayxxi.gub.uy/en/news/article/uruguayan-metabix-biotech-attracts-international-investment-and-plans-global-expansion/", "include", 0.9, "uy-01"),
    ("Seedorina", "UY", "agtech", "Develops robots and digital planters for high-precision agriculture with high-precision seed placement.", "", None, "https://www.uruguayxxi.gub.uy/en/proyectos/", "review", 0.75, "uy-01"),
    ("Baqueano", "UY", "agtech", "Precision livestock recording and data management tool for improving decision-making in livestock operations.", "", None, "https://bidlab.org/en/news/agtech-innovation-action-connecting-startups-producers-and-investment-uruguay", "review", 0.75, "uy-01"),
    ("NurtureField", "UY", "agtech", "Real-time farm data platform serving both small family plots and large agricultural operations.", "", None, "https://bidlab.org/en/news/agtech-innovation-action-connecting-startups-producers-and-investment-uruguay", "review", 0.75, "uy-01"),
    # Colombia
    ("Innmetec", "CO", "medtech", "Digital surgical planning and custom bone implants using hydroxyapatite-polymer composite materials for trauma and tumor reconstruction.", "innmetec.co", 2020, "https://www.crunchbase.com/organization/innmetec", "include", 0.9, "co-01"),
    ("BIIOSMART", "CO", "therapeutics", "Develops intelligent molecular therapeutics (IMT) and medication delivery services for infectious diseases.", "biiosmart.com", None, "https://www.crunchbase.com/organization/biiosmart-technologies", "review", 0.8, "co-01"),
    ("CorpoGen", "CO", "biotech", "Research center specializing in genomics, microbiology, and development of molecular biology kits and scientific services.", "corpogen.org", 1995, "https://en.corpogen.org/", "review", 0.8, "co-01"),
]

import csv
from pathlib import Path

csv_path = Path("staging/discovered_startups.csv")

# Append rows to CSV
with open(csv_path, 'a', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    for startup in new_startups:
        row = [
            startup[0],  # name
            startup[1],  # country_code
            startup[2],  # sector
            startup[3],  # description
            startup[4],  # website
            startup[5] if startup[5] else "",  # founded_year
            startup[6],  # source_url
            startup[7],  # scope_recommendation
            startup[8],  # confidence
            startup[9],  # batch
        ]
        writer.writerow(row)

print(f"Added {len(new_startups)} startups to staging/discovered_startups.csv")
for startup in new_startups:
    print(f"  {startup[1]}: {startup[0]}")
