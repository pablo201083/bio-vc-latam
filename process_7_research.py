import csv

# Mapping from research findings
RESEARCH_FINDINGS = {
    'biocell-mx': {
        'theme': 'Biomaterials & Green Chemistry',
        'description': 'Manufactures patented collagen-based bioingredients (hydrolyzed collagen type II, chondroitin, hyaluronic acid) licensed to CPG manufacturers for nutritional supplements and cosmetics',
        'confidence': 0.95,
        'note': 'Established (1997, 27y). HQ: Irvine, CA (mislabeled as Mexico in dataset)'
    },
    'biofactory-br': {
        'theme': 'Biomanufacturing & Platform Technologies',
        'description': 'World\'s largest biofactory (Curitiba) breeding Aedes aegypti mosquitoes infected with Wolbachia for dengue/chikungunya control. Produces 100M eggs/week for Brazil Ministry of Health',
        'confidence': 0.98,
        'note': 'Scale-up facility (2025). Joint venture: World Mosquito Program + Fiocruz. Government-backed.'
    },
    'bioprocess-automation-brasil-br': {
        'theme': None,
        'description': 'UNVERIFIED - no entity found with this exact name in available databases',
        'confidence': 0.15,
        'note': 'Needs verification against internal database. Related: Biotimize (CDMO), Biotech automation in Brazil.'
    },
    'bioproducts-co': {
        'theme': 'Therapeutics',
        'description': 'LIKELY: Dogma Biotech (Bogota) developing glycosylation technology for protein-based therapeutics. Founded 2023, in UC Berkeley Bakar Bio Labs',
        'confidence': 0.40,  # 0.90 if confirmed as Dogma
        'note': 'Verify if bioproducts-co is Dogma Biotech. If yes: Therapeutics, Startup (2023)'
    },
    'cellculture-br': {
        'theme': None,
        'description': 'UNVERIFIED - no Brazil-based entity found. Research found C3 (Minneapolis, USA) - CDMO for cell culture',
        'confidence': 0.10,
        'note': 'Verify location/name. May be misclassified. Related: JBS biotech center (Florianópolis), Cellertz Bio (cell therapy)'
    },
    'corpogen-co': {
        'theme': 'Diagnostics & Devices',
        'description': 'CorpoGen (established 1995) is a non-profit research center specializing in microbiology, molecular biotechnology, genomic sequencing, and microbiological characterization. Colombian Minciencias-recognized institution',
        'confidence': 0.95,
        'note': 'Established research institute (30y), NOT startup. Collaborates with universities + research institutes.'
    },
    'grupo-bios-co': {
        'theme': 'Bioinputs & Crop Resilience',
        'description': 'Grupo Bios (Colombia) is large agro-industrial conglomerate (formed 2015) operating animal genetics (PIC swine, ABS cattle), animal feed (150K tons/month), poultry production (10K tons/month). 5K-10K employees',
        'confidence': 0.92,
        'note': 'Established conglomerate (2015), NOT startup. Focus: animal genetics + agricultural biotech inputs.'
    }
}

print("PROCESSING 7 RESEARCH FINDINGS\n")

enrichments = []
for startup_id, findings in RESEARCH_FINDINGS.items():
    theme = findings['theme']
    desc = findings['description']
    conf = findings['confidence']

    print(f"{startup_id}:")
    print(f"  Theme: {theme or 'UNVERIFIED'}")
    print(f"  Confidence: {conf}")
    print(f"  Note: {findings['note']}\n")

    # Only add enrichments for verified startups (confidence >= 0.90) or partial data (0.4-0.9)
    if theme and conf >= 0.40:
        enrichments.append({
            'entity_id': startup_id,
            'table_name': 'startup_extended',
            'field_name': 'bio_theme_primary',
            'new_value': theme,
            'source_url': 'https://research.biolatam.io/deep-research-ecuador-7',
            'confidence': min(conf, 1.0),
            'notes': findings['note']
        })

        enrichments.append({
            'entity_id': startup_id,
            'table_name': 'startup_extended',
            'field_name': 'business_one_liner',
            'new_value': desc[:150],
            'source_url': 'https://research.biolatam.io/deep-research-ecuador-7',
            'confidence': min(conf, 1.0),
            'notes': findings['note']
        })

# Save enrichments
out_path = 'staging/entity_enrichments.csv'
with open(out_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['entity_id', 'table_name', 'field_name', 'new_value', 'source_url', 'confidence', 'notes'])
    writer.writeheader()
    for e in enrichments:
        writer.writerow(e)

print(f"\n{'='*70}")
print(f"ENRICHMENTS SAVED: {len(enrichments)} records")
print(f"Path: {out_path}")
print(f"\nBreakdown:")
print(f"  - Verified (conf >= 0.90): 3 startups (biocell, biofactory, corpogen, grupo_bios)")
print(f"  - Partial (conf 0.40-0.89): 1 startup (bioproducts if Dogma)")
print(f"  - Unverified (conf < 0.40): 3 startups (cellculture, bioprocess, bioproducts if not Dogma)")
print(f"\nNext: ingest + re-cluster")
