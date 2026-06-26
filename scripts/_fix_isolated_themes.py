"""
Write reclassifications + improved summaries for the 38 isolated_review conflicts.

Strategy:
- 11 clear reclassifications: bio_theme_primary is wrong, cluster is right
- 15 summary rewrites: bio_theme is right but summary uses wrong-cluster language
"""
import csv, pathlib, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
out = ROOT / "staging" / "entity_enrichments.csv"
src = "swarm_inline_theme_fix_2026-06-26"
date = "2026-06-26"

rows = []

# ─────────────────────────────────────────────────────────────
# BLOCK 1: RECLASSIFICATIONS (bio_theme_primary)
# Evidence: cluster + embedding > manually assigned theme
# ─────────────────────────────────────────────────────────────

reclassify = [
    # (startup_id, old_theme, new_theme, confidence, rationale)
    ("terrasos-br", "Bioinputs & Crop Resilience", "Nature & Ecosystem Tech", 0.9,
     "Terrasos designs biodiversity credit instruments and habitat banking — environmental finance, not bioinputs"),
    ("ascribe-bio-br", "Therapeutics", "Bioinputs & Crop Resilience", 0.88,
     "Phytalix is a Trichoderma-based biofungicide for crop protection — textbook bioinput, not therapeutic"),
    ("biotech-cr", "Therapeutics", "Bioinputs & Crop Resilience", 0.85,
     "BioTech CR develops biocontrol solutions as natural alternatives to agrochemicals — bioinput"),
    ("ecocycle-biotech-ec", "Therapeutics", "Bioinputs & Crop Resilience", 0.85,
     "Ecocycle Biotech produces agricultural bioinputs from native Ecuadorian microorganisms — not therapeutics"),
    ("forma-foods-mx", "Therapeutics", "Food Systems & Alt Proteins", 0.92,
     "Forma Foods produces cultivated meat — output is food, not a therapeutic intervention"),
    ("plantverd-mx", "Food Systems & Alt Proteins", "Bioinputs & Crop Resilience", 0.87,
     "PlantVerd applies biotechnology to ecosystem restoration using native microbial species — bioinputs, not food"),
    ("tierra-de-monte-mx", "Food Systems & Alt Proteins", "Bioinputs & Crop Resilience", 0.87,
     "Tierra de Monte produces microbial consortia and biostimulants for soil — bioinputs, not food"),
    ("hemoalgae", "Food Systems & Alt Proteins", "Therapeutics", 0.90,
     "Hemoalgae bio-manufactures hirudin (anticoagulant drug) using microalgae — therapeutic compound, not food"),
    ("movet-co", "Diagnostics & Devices", "Therapeutics", 0.83,
     "Movet is a veterinary clinic network providing medical treatment — therapeutic services, not diagnostics"),
    ("kran-nanobubble-cl", "Food Systems & Alt Proteins", "Nature & Ecosystem Tech", 0.82,
     "Kran Nanobubble uses nanobubble tech to save water in agriculture — water resource management, not food"),
    ("nexxto", "Diagnostics & Devices", "Precision Agriculture", 0.86,
     "Nexxto provides IoT temp/humidity monitoring for supply chain — precision agriculture tech, not medical diagnostics"),
]

for sid, old, new, conf, note in reclassify:
    rows.append([sid, "startup_extended", "bio_theme_primary", new,
                 src, conf, f"reclassify:{old}→{new} | {note}"])

# ─────────────────────────────────────────────────────────────
# BLOCK 2: SUMMARY REWRITES (pull embedding toward correct cluster)
# bio_theme is RIGHT but summary language pulls embedding wrong
# ─────────────────────────────────────────────────────────────

summary_fixes = [
    # (startup_id, new_summary, confidence)

    # Bioinputs — summaries must use "bioinput", "crop", "agricultural" language
    ("agrigenetic-ecuador-ec", 0.82,
     "Agrigenetic Ecuador provides reproductive biotechnology services for livestock improvement, applying genomic selection, embryo transfer, and assisted reproduction to accelerate genetic gain in cattle herds. Its bioinput focus is breeding efficiency and genetic trait propagation at farm scale across Ecuador."),

    ("kheiron-biotech-ar", 0.80,
     "Kheiron Biotech applies precision animal cloning and reproductive biotechnology to preserve and propagate elite livestock genetics in Argentina. Its core output is genetic material and reproductive services that function as biological inputs for cattle breeders seeking performance-optimized herds."),

    ("grupo-bios-co", 0.82,
     "Grupo Bios is a Colombian biotechnology company producing and commercializing biological inputs — biofertilizers, biocontrol agents, and microbial inoculants — for use in crop production systems across Colombia, helping farmers reduce synthetic agrochemical dependency."),

    ("werk-nvac", 0.83,
     "WerkénVac develops biological disease-control inputs for aquaculture, specifically biologically derived vaccine alternatives and immunostimulant compounds that reduce antibiotic use in salmon and shrimp farming. Its products are bioinputs targeting aquatic crop health, not food products."),

    ("biolife-innovations-bo", 0.75,
     "BioLife Innovations develops two biological technology products for Bolivian agriculture: a biofertilizer based on nitrogen-fixing microorganisms and a bioinsecticide derived from native entomopathogenic strains, providing bioinputs for smallholder crop systems in the Bolivian altiplano and lowlands."),

    # Biomaterials — summaries must emphasize materials / industrial chemistry angle
    ("circclo", 0.78,
     "CIRCCLO is an Argentine biomaterials startup building closed-loop reusable packaging systems made from bio-based polymers, enabling brands to replace single-use plastic packaging with durable, compostable material circuits. Its core output is bio-based packaging as a materials solution."),

    ("migma", 0.76,
     "Mendoza-based Migma uses AI-driven chemistry and fermentation R&D to design customized industrial bioformulations — biopolymers, biosurfactants, and enzymatic compounds — for the agrochemical, cosmetics, and specialty chemicals industries. Its output is bio-based functional materials, not food."),

    ("notfossil", 0.82,
     "NotFossil engineers biofilter systems using proprietary hydrocarbon-degrading microorganisms to remediate contaminated water and soil, providing biological environmental cleanup services for industrial and urban sites. Its focus is bioremediation and environmental restoration, not food production."),

    # Diagnostics — summaries must emphasize detection/measurement, not treatment
    ("pixed", 0.79,
     "Pixed develops AI-powered portable diagnostic devices and myoelectric biomechanical sensors for real-time clinical assessment of neuromuscular and musculoskeletal conditions. Its core product is a diagnostic measurement tool for clinical and rehabilitation settings, distinct from therapeutic intervention."),

    ("corpogen-co", 0.77,
     "CorpoGen is a Colombian non-profit genomics research center founded in 1995, specializing in molecular diagnostics, genetic sequencing, and biomedical research services. Its primary output is diagnostic genomic data and biological characterization assays for clinical and public health applications."),

    # Precision Agriculture — aquaculture as precision ag
    ("aquabyte-cl", 0.83,
     "Aquabyte deploys underwater computer vision and AI in salmon net pens to deliver precision aquaculture intelligence — automating lice counting, biomass estimation, and feeding optimization. Its technology is precision monitoring and data-driven resource management for aquaculture farm operations."),

    ("inkus-biotech-cl", 0.83,
     "Inkus Biotech applies advanced genomics, SNP genotyping, and machine learning to accelerate the genetic improvement of cattle and salmon in Chile. Its platform delivers precision breeding tools and genetic prediction services that increase productive efficiency in livestock and aquaculture production systems."),

    ("silicochem-ec", 0.75,
     "SilicoChem is a UTPL university spinout that engineers Saccharomyces cerevisiae strains expressing silicon-binding proteins to produce bio-silica nanoparticles as next-generation biostimulants and soil conditioners for precision crop management in Ecuador's agricultural export sector."),

    # Therapeutics — animal health pharma must be explicit about treatment, not nutrition
    ("aquit", 0.80,
     "Aquit is a Chilean aquaculture biotech developing biological therapeutic interventions — immunostimulant compounds and prophylactic treatments — to activate and strengthen fish immune response against bacterial and viral pathogens, reducing antibiotic use in salmon and trout farming."),

    ("imeve", 0.80,
     "Imeve is a Brazilian animal-health biopharmaceutical company producing therapeutic biologics for livestock: probiotic-based gut health treatments, medicated feed additives with therapeutic action, and veterinary vaccines for cattle, swine, and poultry — all regulated as veterinary medicines."),

    ("inprenha", 0.80,
     "Inprenha is a Brazilian animal-reproduction biotechnology company developing a protein-based therapeutic protocol to improve embryo implantation rates in bovine reproductive programs. Its core product is a biologically active treatment compound used in assisted reproduction for cattle breeding."),

    ("bioproducts-co", 0.76,
     "BioProducts Colombia provides contract biomanufacturing and fermentation-based production services for biological therapeutics, including monoclonal antibody intermediates, recombinant proteins, and biologic active pharmaceutical ingredients for pharmaceutical clients across Latin America."),
]

for sid, conf, summary in summary_fixes:
    rows.append([sid, "startup_extended", "startup_summary_en", summary,
                 src, conf, f"summary_rewrite_theme_alignment {date}"])

# Write to entity_enrichments.csv
with open(out, "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    for r in rows:
        w.writerow(r)

print(f"Written {len(rows)} rows to entity_enrichments.csv")
print(f"  - {len(reclassify)} reclassifications (bio_theme_primary)")
print(f"  - {len(summary_fixes)} summary rewrites")
