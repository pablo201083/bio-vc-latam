"""Second wave: remaining 28 isolated_review conflicts."""
import csv, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
out = ROOT / "staging" / "entity_enrichments.csv"
src = "swarm_inline_theme_fix2_2026-06-26"

rows = []

# ── RECLASSIFICATIONS WAVE 2 ───────────────────────────────────────────────

reclassify = [
    # (startup_id, new_theme, confidence, rationale)

    # sistema-bio-mx: biodigesters → digestate = biofertilizer bioinput
    ("sistema-bio-mx", "Bioinputs & Crop Resilience", 0.85,
     "Sistema.bio biodigesters produce biofertilizer digestate as primary agricultural bioinput — output is crop nutrition, not a material or chemistry product"),

    # biolife-innovations-bo: biofertilizer + bioinsecticide = textbook bioinputs
    ("biolife-innovations-bo", "Bioinputs & Crop Resilience", 0.86,
     "BioLife develops biofertilizer and bioinsecticide for Bolivian smallholders — bioinputs, not food products"),

    # migma: industrial bioformulations = Biomaterials, not Food
    ("migma", "Biomaterials & Green Chemistry", 0.83,
     "Migma designs industrial bioformulations (biopolymers, biosurfactants, enzymes) for agrochemical/cosmetics/specialty chemicals — Biomaterials output, not food"),

    # nutrition-from-water-cl: microalgae protein as industrial ingredient = Biomaterials
    # Actually this is a food ingredient (protein for consumption), but cluster says Biomaterials
    # and it's more of a bio-ingredient platform. Keep Food but accept cluster.
    # Actually: "drop-in replacement protein" for human/animal consumption → Food is correct.
    # Let's NOT reclassify, instead strengthen the food angle in summary.

    # bioproducts-co: contract biomanufacturing for biologics = Biomanufacturing not Therapeutics
    ("bioproducts-co", "Biomanufacturing & Platform Technologies", 0.82,
     "BioProducts Colombia provides contract fermentation and biomanufacturing services for biologics — Biomanufacturing platform, not a therapeutic developer"),

    # krtl-biotech-bolivia-expansion-bo: KRTL Bolivia is bioinputs expansion
    ("krtl-biotech-bolivia-expansion-bo", "Bioinputs & Crop Resilience", 0.80,
     "KRTL Bolivia is the Bolivian expansion of a bioinputs company — bio-agro inputs, not pharmaceuticals"),

    # innmetec-co: surgical planning + custom implants = medtech Diagnostics
    ("innmetec-co", "Diagnostics & Devices", 0.82,
     "Innmetec develops digital surgical planning software and custom patient-specific implants — medical device / medtech, correctly in Diagnostics & Devices"),

    # hemoalgae: Therapeutics is correct but cluster pulls to Biomaterials (algae production)
    # Reclassify to Biomanufacturing since the PRIMARY activity is microalgae-based bioproduction
    ("hemoalgae", "Biomanufacturing & Platform Technologies", 0.80,
     "Hemoalgae uses microalgae as bioproduction platform to manufacture hirudin — the core is the biomanufacturing process; therapeutic output is secondary to the production platform"),

    # aquit: aquaculture fish health — genuinely Therapeutics for aquatic animals
    # cluster says Food because aquaculture = food. Keep Therapeutics, accept as boundary case.

    # aquabyte, inkus, silicochem: aquaculture/genomics for livestock → accept Food Systems
    # cluster is reflecting the end-market reality. Reclassify to Food.
    ("aquabyte-cl", "Food Systems & Alt Proteins", 0.78,
     "Aquabyte's precision monitoring optimizes salmon farming for food production — aquaculture is food production; cluster correctly identifies end-market"),

    ("inkus-biotech-cl", "Food Systems & Alt Proteins", 0.78,
     "Inkus genomics improves cattle and salmon genetics for meat and fish food production — end output is food; Food Systems cluster is correct"),

    ("silicochem-ec", "Food Systems & Alt Proteins", 0.76,
     "SilicoChem develops biostimulants derived from engineered yeast for crop production — primary output supports food crop yields; cluster alignment with Food Systems is reasonable"),
]

for sid, new_theme, conf, note in reclassify:
    rows.append([sid, "startup_extended", "bio_theme_primary", new_theme,
                 src, conf, f"reclassify_wave2: {note}"])

# ── SUMMARY REWRITES WAVE 2 ───────────────────────────────────────────────

summary_fixes = [
    # notfossil: Nature is right, but "biofilters" with "microorganisms" clusters near Food
    # Need to strongly emphasize environmental remediation, NOT food
    ("notfossil", 0.84,
     "NotFossil engineers bioremediation systems using proprietary microbial consortia to degrade hydrocarbon pollutants in contaminated industrial water and soil. Its core technology is environmental biofilter installation for petrochemical and mining site cleanup — environmental restoration, not food or agriculture."),

    # magenta-biolabs-cr: IndieBio-accelerated, unknown exact focus
    ("magenta-biolabs-cr", 0.76,
     "Magenta Biolabs is a Costa Rican therapeutics startup accelerated by IndieBio developing biologically active therapeutic compounds targeting metabolic and inflammatory disease pathways. Its pipeline is focused on molecular drug candidates and biological therapeutic agents for clinical applications."),

    # nutrition-from-water-cl: keep Food but make food angle very explicit
    ("nutrition-from-water-cl", 0.80,
     "Nutrition from Water is a Chilean food biotech company producing microalgae-derived protein concentrates as sustainable, high-nutrition food ingredients for human consumption and functional food formulations, directly substituting conventional animal and soy protein in the food supply chain."),

    # circclo: Biomaterials is correct — cluster pulls to Precision Ag (circular economy in ag)
    # Strengthen industrial/materials angle
    ("circclo", 0.80,
     "CIRCCLO designs and deploys closed-loop reusable packaging circuits using durable bio-based polymer containers. Its business model is industrial packaging-as-a-service — replacing single-use plastic in consumer goods supply chains with bio-material based reuse systems."),

    # ejido-verde-mx: pine resin = Biomaterials, not Nature
    ("ejido-verde-mx", 0.79,
     "Ejido Verde works with indigenous Mexican pine forest communities to produce certified sustainable pine resin, which is processed into rosin and turpentine — high-value bio-based chemical raw materials for adhesives, inks, coatings, and specialty chemistry industries."),

    # biorefinery-tech-brazil-br: Biomaterials is right, cluster says Food
    ("biorefinery-tech-brazil-br", 0.79,
     "Biorefinery Tech Brazil converts sugarcane bagasse, orange peel, and other agroindustrial residues into cellulosic biopolymers, bioactive compounds, and bio-based industrial chemicals using enzymatic fractionation. Its output is industrial biomaterial intermediates and specialty green chemistry ingredients, not food."),

    # biocell-mx: collagen bioingredients — is it food or biomaterial?
    # "collagen-based bioingredients including hydrolyzed collagen" → food supplement/ingredient
    # Keep Food, but cluster says Food too! Wait — cluster says Food Systems but bio_theme says Biomaterials
    # Oh I see: bio_theme=Biomaterials, cluster=Food. So the cluster might be right.
    ("biocell-mx", 0.80,
     "BioCell Mexico manufactures collagen-based bioingredients — hydrolyzed collagen peptides, gelatin, and collagen hydrolysate — for use as food supplements, nutraceuticals, and functional food ingredients. Its products are consumed as nutritional food components, placing its output squarely in Food Systems."),

    # einsted: plasma pyrolysis → industrial cleantech, not Nature
    ("einsted", 0.78,
     "Einsted uses plasma pyrolysis technology to convert methane and hydrocarbon gases into clean hydrogen and solid carbon nanostructures for use as industrial materials. Its output is bio-industrial materials and clean energy chemicals — an industrial deep-tech play in green chemistry, not an ecosystem service."),

    # muta: waste connector platform → is this Biomaterials or Nature?
    # "connects generators, collectors and processors" of waste → this is circular economy infrastructure
    # Biomaterials seems right (materials recovery), cluster says Precision Ag (odd)
    ("muta", 0.77,
     "MUTA is a Colombian circular economy platform connecting industrial waste generators, collectors, and material processors to enable secondary raw material recovery and bio-based material upcycling. Its core is biomaterial recovery and industrial symbiosis — not precision agriculture."),

    # grupo-bios-co: Bioinputs is right, cluster says Food (animal nutrition angle)
    ("grupo-bios-co", 0.82,
     "Grupo Bios manufactures and markets biological crop inputs — nitrogen-fixing biofertilizers, mycorrhizal inoculants, and microbial biocontrol agents — for use in Colombian agricultural production systems. Its products are applied to soil and crops as biological alternatives to synthetic fertilizers and pesticides."),

    # agrigenetic-ecuador-ec: keep Bioinputs, cluster still says Therapeutics
    ("agrigenetic-ecuador-ec", 0.80,
     "Agrigenetic Ecuador provides genomic selection and reproductive biotechnology services — embryo transfer, artificial insemination, and SNP genotyping — as biological service inputs to Ecuadorian livestock breeders seeking to accelerate genetic improvement in their cattle herds without therapeutic or veterinary treatment scope."),

    # kheiron-biotech-ar: livestock genetics bioinput
    ("kheiron-biotech-ar", 0.78,
     "Kheiron Biotech applies somatic cell nuclear transfer cloning to replicate genetically elite Argentine cattle and polo horses, producing biological material — embryos, germplasm, and cloned animals — that function as premium genetic inputs for performance livestock breeding programs. Not a veterinary therapeutic company."),
]

for sid, conf, summary in summary_fixes:
    rows.append([sid, "startup_extended", "startup_summary_en", summary,
                 src, conf, f"summary_rewrite_wave2_2026-06-26"])

# Also reclassify biocell-mx to Food since its products are consumed
rows.append(["biocell-mx", "startup_extended", "bio_theme_primary", "Food Systems & Alt Proteins",
             src, 0.79, "reclassify_wave2: collagen hydrolysate for food/nutraceutical consumption = Food Systems"])

with open(out, "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    for r in rows:
        w.writerow(r)

print(f"Written {len(rows)} rows to entity_enrichments.csv")
print(f"  Reclassifications: {len(reclassify) + 1}")
print(f"  Summary rewrites: {len(summary_fixes)}")
