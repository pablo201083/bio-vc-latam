# Semantic Single-Level Sweep

- Universe: include + confirmed only
- Startups clustered: 283
- Candidate k values tested: 5, 6, 7, 8, 9, 10, 11, 12
- Recommended single-level k: 12
- Recommended explainability score: 54.2
- Source-backed manual semantic overrides applied to operational assignments: 25

## Candidate comparison

- profile=balanced, k=5: explainability=50.4, avg_margin=18, avg_within=28, low_conf_share=5.3%, unique_labels=5, label_compression=1, size_cv=0.43, largest_cluster_share=33.2%
- profile=balanced, k=6: explainability=49.7, avg_margin=17.5, avg_within=29.3, low_conf_share=4.2%, unique_labels=6, label_compression=1, size_cv=0.49, largest_cluster_share=29%
- profile=balanced, k=7: explainability=50.9, avg_margin=19, avg_within=30.9, low_conf_share=3.2%, unique_labels=7, label_compression=1, size_cv=0.48, largest_cluster_share=24.7%
- profile=balanced, k=8: explainability=52.6, avg_margin=19.4, avg_within=32.4, low_conf_share=7.4%, unique_labels=8, label_compression=1, size_cv=0.38, largest_cluster_share=22.3%
- profile=balanced, k=9: explainability=51.7, avg_margin=19.7, avg_within=33.3, low_conf_share=6.4%, unique_labels=9, label_compression=1, size_cv=0.46, largest_cluster_share=20.8%
- profile=balanced, k=10: explainability=54, avg_margin=21.3, avg_within=35.1, low_conf_share=5.3%, unique_labels=10, label_compression=1, size_cv=0.37, largest_cluster_share=14.8%
- profile=balanced, k=11: explainability=53.6, avg_margin=22.1, avg_within=36.1, low_conf_share=5.7%, unique_labels=11, label_compression=1, size_cv=0.43, largest_cluster_share=14.5%
- profile=balanced, k=12: explainability=54.2, avg_margin=23.5, avg_within=37.3, low_conf_share=5.7%, unique_labels=12, label_compression=1, size_cv=0.44, largest_cluster_share=13.4%
- profile=industry_heavy, k=5: explainability=50.4, avg_margin=18.4, avg_within=28, low_conf_share=6%, unique_labels=5, label_compression=1, size_cv=0.44, largest_cluster_share=32.9%
- profile=industry_heavy, k=6: explainability=49.4, avg_margin=19.3, avg_within=29.5, low_conf_share=7.1%, unique_labels=6, label_compression=1, size_cv=0.53, largest_cluster_share=32.9%
- profile=industry_heavy, k=7: explainability=50.4, avg_margin=21.2, avg_within=31.5, low_conf_share=8.1%, unique_labels=7, label_compression=1, size_cv=0.53, largest_cluster_share=29%
- profile=industry_heavy, k=8: explainability=52.3, avg_margin=21, avg_within=33, low_conf_share=10.2%, unique_labels=8, label_compression=1, size_cv=0.41, largest_cluster_share=20.5%
- profile=industry_heavy, k=9: explainability=50.7, avg_margin=21.1, avg_within=33.8, low_conf_share=8.8%, unique_labels=9, label_compression=1, size_cv=0.54, largest_cluster_share=21.2%
- profile=industry_heavy, k=10: explainability=51.7, avg_margin=22.3, avg_within=35.2, low_conf_share=6%, unique_labels=10, label_compression=1, size_cv=0.54, largest_cluster_share=20.8%
- profile=industry_heavy, k=11: explainability=51.2, avg_margin=22.9, avg_within=36, low_conf_share=7.1%, unique_labels=11, label_compression=1, size_cv=0.59, largest_cluster_share=19.8%
- profile=industry_heavy, k=12: explainability=53.1, avg_margin=23.6, avg_within=37.4, low_conf_share=5.7%, unique_labels=12, label_compression=1, size_cv=0.51, largest_cluster_share=16.3%
- profile=technology_heavy, k=5: explainability=50.5, avg_margin=16.6, avg_within=27.2, low_conf_share=8.8%, unique_labels=5, label_compression=1, size_cv=0.37, largest_cluster_share=33.6%
- profile=technology_heavy, k=6: explainability=49.3, avg_margin=17.3, avg_within=28.4, low_conf_share=7.4%, unique_labels=6, label_compression=1, size_cv=0.49, largest_cluster_share=30.7%
- profile=technology_heavy, k=7: explainability=49.4, avg_margin=18.1, avg_within=29.8, low_conf_share=7.4%, unique_labels=7, label_compression=1, size_cv=0.51, largest_cluster_share=26.9%
- profile=technology_heavy, k=8: explainability=50.6, avg_margin=18.8, avg_within=31.3, low_conf_share=6.7%, unique_labels=8, label_compression=1, size_cv=0.48, largest_cluster_share=22.6%
- profile=technology_heavy, k=9: explainability=49.9, avg_margin=19.4, avg_within=32.2, low_conf_share=7.8%, unique_labels=9, label_compression=1, size_cv=0.54, largest_cluster_share=21.9%
- profile=technology_heavy, k=10: explainability=51.7, avg_margin=20.9, avg_within=33.8, low_conf_share=5.7%, unique_labels=10, label_compression=1, size_cv=0.49, largest_cluster_share=19.1%
- profile=technology_heavy, k=11: explainability=51, avg_margin=21.3, avg_within=34.7, low_conf_share=6%, unique_labels=11, label_compression=1, size_cv=0.56, largest_cluster_share=19.1%
- profile=technology_heavy, k=12: explainability=53.4, avg_margin=22.8, avg_within=36.2, low_conf_share=7.8%, unique_labels=12, label_compression=1, size_cv=0.45, largest_cluster_share=14.1%

## Adopted k=12 taxonomy

- Operational assignments use the recommended single-level semantic cut (balanced, k=12), so the visible taxonomy stays source-backed, comparable across startups and free of macro/micro nesting.

### agri intelligence and traceable markets (37)
- Description: Agronomic decisioning, traceability and material coordination of agri-food chains.
- Dominant macro: precision agriculture and resource intelligence
- Top tokens: data; agtech; animal; proteins; dairy; crop; precision; intelligence
- Representatives: Eiwa; Dymaxion Labs; @Tech; JetBov
- Avg margin: 16.4
- Low confidence: 5
- Naming status: auto
- Credibility score: 86
- Fit review/watch: 5/0

### ag biologicals and crop resilience (36)
- Description: Biological inputs and productive resilience for agricultural systems.
- Dominant macro: ag biologicals and crop resilience
- Top tokens: crop; biological; biologicals; resilience; plant; monitoring; control; climate
- Representatives: Infira; Neocrop Technologies; Semion; Promip
- Avg margin: 20.7
- Low confidence: 4
- Naming status: auto
- Credibility score: 89
- Fit review/watch: 4/0

### clinical diagnostics and medical devices (33)
- Description: Diagnostics, detection and clinical devices.
- Dominant macro: diagnostics and medtech
- Top tokens: diagnostics; medtech; molecular; treatment; human; analysis; public; detection
- Representatives: Samay; Bleps Vision; Embryoxite; Tell
- Avg margin: 31.4
- Low confidence: 0
- Naming status: auto
- Credibility score: 100
- Fit review/watch: 0/0

### therapeutics and regenerative bio (31)
- Description: Therapeutics, biological delivery and regenerative medicine.
- Dominant macro: therapeutics and regenerative medicine
- Top tokens: therapeutics; medicine; drug; wound; regenerative; public; evidence; tissue
- Representatives: Radbio; Momentum Therapeutics; Tesabio.ai; Ardan
- Avg margin: 14
- Low confidence: 5
- Naming status: auto
- Credibility score: 86
- Fit review/watch: 5/0

### resource recovery and remediation (29)
- Description: Material recovery, loop closure and remediation.
- Dominant macro: climate, energy and resource systems
- Top tokens: carbon; nature; restoration; biodiversity; energy; intelligence; climate; satellite
- Representatives: Nideport; Ruuts; Carbonext; Poás Bioenergy
- Avg margin: 28.3
- Low confidence: 0
- Naming status: auto
- Credibility score: 100
- Fit review/watch: 0/0

### food ingredients and biofactories (28)
- Description: Food ingredients, fermentation and biofactory systems.
- Dominant macro: food biotech and novel ingredients
- Top tokens: ingredients; plant; aquaculture; animal; compounds; peces; human; foodtech
- Representatives: MicroTerra; Cellva; Tomorrow Foods; GlycoX
- Avg margin: 24.6
- Low confidence: 0
- Naming status: auto
- Credibility score: 100
- Fit review/watch: 0/0

### grain traceability and producer infrastructure (25)
- Description: Digital infrastructure for traceability, seeds, grains, growers and commercial coordination across agri-food chains.
- Dominant macro: climate, energy and resource systems
- Top tokens: growers; credit; traceability; digital; agro; risk; producer; access
- Representatives: Traive; Agrotoken; Tracestory; Agricapital
- Avg margin: 26.6
- Low confidence: 0
- Naming status: auto
- Credibility score: 100
- Fit review/watch: 0/0

### drug discovery and disease therapeutics (22)
- Description: Therapeutic discovery, complex-disease platforms, cancer biology and biological delivery.
- Dominant macro: therapeutics and regenerative medicine
- Top tokens: cells; therapeutics; proteins; cancer; therapy; disease; regenerative; ingredients
- Representatives: Ayuvant; OMICS; Circa Therapeutics; ArgenTAG
- Avg margin: 23.8
- Low confidence: 1
- Naming status: auto
- Credibility score: 96
- Fit review/watch: 1/0

### biobased materials and waste valorization (14)
- Description: Biomaterials, biobased chemistry and waste valorization into circular materials or inputs.
- Dominant macro: biobased chemistry and advanced materials
- Top tokens: biomaterials; packaging; waste; replace; plastics; circular; applications; surfaces
- Representatives: Patagon Fiber; Mycorium Biotech; BioPlaster Research Inc; BioPlaster Research
- Avg margin: 31.1
- Low confidence: 0
- Naming status: auto
- Credibility score: 100
- Fit review/watch: 0/0

### biomanufacturing and molecular platforms (13)
- Description: Biological production and enabling molecular tools.
- Dominant macro: biomanufacturing and bioindustrial platforms
- Top tokens: fermentation; enzymes; precision; proteins; ingredients; biotechnology; animal; stable
- Representatives: APEXzymes; Enzyva; Bioplastix; BreakPET
- Avg margin: 26
- Low confidence: 1
- Naming status: auto
- Credibility score: 93
- Fit review/watch: 1/0

### biobased chemistry and circular materials (8)
- Description: Biomaterials and circular chemistry based on biological inputs.
- Dominant macro: biobased chemistry and advanced materials
- Top tokens: chemicals; percent; fresh; vertical; vegetables; skin; public; profile
- Representatives: BioBlends; Unibaio; Tintte; Pink Farms
- Avg margin: 28.4
- Low confidence: 0
- Naming status: auto
- Credibility score: 100
- Fit review/watch: 0/0

### bioactive products and regenerative edge cases (7)
- Description: Bioactive or regenerative cases mixing health, cosmetics, food or agriculture that are not pure therapeutics.
- Dominant macro: therapeutics and regenerative medicine
- Top tokens: chemistry; molecular; land; eutectic; energy; design; critical; cosmetics
- Representatives: Eywa Biotech; Alkemio; Monte Caldera Technology; Bioeutectics
- Avg margin: 29.6
- Low confidence: 0
- Naming status: auto
- Credibility score: 100
- Fit review/watch: 0/0

