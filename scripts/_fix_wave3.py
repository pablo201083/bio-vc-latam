"""Wave 3: targeted reclassifications + rewrites for remaining 29 conflicts."""
import csv, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
out = ROOT / "staging" / "entity_enrichments.csv"
src = "swarm_inline_theme_fix3_2026-06-26"

rows = []

# ── RECLASSIFICATIONS ──────────────────────────────────────────────────────

reclassify = [
    # michroma: fungal pigments for food = Food Systems, not Biomaterials
    ("michroma", "Food Systems & Alt Proteins", 0.84,
     "Michroma produces natural fungal-derived pigments as food colorants — output is consumed as food ingredient"),

    # werk-nvac: aquaculture disease control in food production context
    ("werk-nvac", "Food Systems & Alt Proteins", 0.78,
     "WerkénVac biological inputs serve aquaculture salmon farming — end market is food production, cluster correctly reflects this"),

    # movet-co: veterinary diagnostics + clinical network = Diagnostics, not Therapeutics
    ("movet-co", "Diagnostics & Devices", 0.82,
     "Movet is a veterinary diagnostic clinic network — standardized diagnostics and health monitoring, correctly in Diagnostics & Devices"),

    # fermentlab-br: precision fermentation platform = Biomanufacturing, not Food
    ("fermentlab-br", "Biomanufacturing & Platform Technologies", 0.83,
     "FermentLab is a fermentation R&D platform and CDMO — produces biologics at scale, not finished food products"),

    # fermentlabs-co: same — platform, not food product
    ("fermentlabs-co", "Biomanufacturing & Platform Technologies", 0.83,
     "FermentLabs Colombia is a precision fermentation biomanufacturing platform — cluster is right"),

    # nat4bio: bio-nutrition for crops = Bioinputs
    ("nat4bio", "Bioinputs & Crop Resilience", 0.80,
     "Nat4Bio develops bionutrition and biostimulant products for crops — bioinputs, not food for human consumption"),

    # huiro: Chilean seaweed biostimulant = Bioinputs
    ("huiro", "Bioinputs & Crop Resilience", 0.81,
     "Huiro processes Chilean kelp/seaweed into liquid biostimulants for crop production — agricultural bioinput"),

    # poas_bioenergy: biogas/bioenergy from waste = Biomaterials (energy materials)
    ("poas_bioenergy", "Biomaterials & Green Chemistry", 0.79,
     "Poas Bioenergy converts organic waste to biogas and bioenergy — bio-based energy material output, not ecosystem service"),

    # biogenesis-bago-ec: veterinary biologics for livestock = Bioinputs (disease prevention inputs)
    ("biogenesis-bago-ec", "Bioinputs & Crop Resilience", 0.78,
     "Biogenesis Bago veterinary biologics (vaccines, antiparasitics) are biological health inputs for livestock production — bioinputs for animal agriculture"),

    # amplify-dynamics: bioprocess optimization platform = Biomanufacturing
    ("amplify-dynamics", "Biomanufacturing & Platform Technologies", 0.80,
     "Amplify Dynamics optimizes bioprocesses for biologics production — Biomanufacturing platform, cluster is right"),

    # biohack-uio-ec: community biolab and maker space = Biomanufacturing platform
    ("biohack-uio-ec", "Biomanufacturing & Platform Technologies", 0.76,
     "BioHack UIO is Ecuador's first community biolab providing open biomanufacturing infrastructure — platform, not therapeutics"),

    # scintia-mx: biotech education platform → actually not clearly therapeutics
    # scintia makes educational biotech kits/labs — could be Biomanufacturing (lab tools)
    ("scintia-mx", "Biomanufacturing & Platform Technologies", 0.72,
     "Scintia develops educational biotechnology laboratory kits and bioprocess learning platforms — biomanufacturing tools and infrastructure"),

    # solfium: bio-based solar/energy materials = Biomaterials (energy chemistry)
    ("solfium", "Biomaterials & Green Chemistry", 0.78,
     "Solfium develops bio-based materials for solar energy applications — green chemistry and bio-derived energy materials"),

    # merken-biotech-cl: if cluster says Diagnostics, likely right
    ("merken-biotech-cl", "Diagnostics & Devices", 0.76,
     "Merken Biotech develops biomarker-based diagnostic tools — Diagnostics & Devices cluster is correct"),
]

for sid, new_theme, conf, note in reclassify:
    rows.append([sid, "startup_extended", "bio_theme_primary", new_theme,
                 src, conf, f"reclassify_wave3: {note}"])

# ── SUMMARY REWRITES (boundary cases — push embedding) ────────────────────

summary_fixes = [
    # ejido-verde-mx: pine resin chemistry = Biomaterials, push away from Bioinputs
    ("ejido-verde-mx", 0.79,
     "Ejido Verde partners with indigenous Mexican communities to sustainably harvest pine resin, which it refines into rosin esters, terpene solvents, and turpentine — high-value bio-based specialty chemicals sold into adhesives, coatings, ink, and industrial chemistry markets. Output is green chemistry raw material, not an agricultural bioinput."),

    # michroma: make food colorant angle explicit (already reclassified above)
    ("michroma", 0.84,
     "Michroma is a Chilean food biotechnology company using fungal fermentation to produce natural pigments — red, orange, and yellow food colorants — as sustainable alternatives to synthetic dyes in food and beverage formulations. Its products are certified food ingredients for direct human consumption."),

    # notfossil: bioremediation not food — very explicit
    ("notfossil", 0.85,
     "NotFossil engineers site-specific bioremediation systems using consortia of hydrocarbon-degrading microorganisms to clean petroleum-contaminated industrial soil and water. Deploys biofilter installations at oil field sites and refineries for regulatory environmental compliance. Has no food, agriculture, or crop production application."),

    # cryosmetics: likely cosmetics biomaterials
    ("cryosmetics", 0.75,
     "Cryosmetics develops bio-derived active ingredients for cosmetic and dermocosmetic formulations using cryopreservation and bioextraction technology. Its outputs are biological raw materials — plant stem cell extracts, cryo-stabilized bioactives — used as cosmetic ingredients, placing it in the biomaterials and green chemistry category."),

    # fabns: nano biosensors = diagnostics, push away from biomaterials
    ("fabns", 0.76,
     "FabNS develops nanoscale biosensor platforms for real-time detection of pathogens, toxins, and biomarkers in clinical and environmental samples. Its core product is a diagnostic sensing device, not a material or chemical — detection and measurement is the primary output."),

    # nanomedical-cr: nano drug delivery = therapeutics or diagnostics
    ("nanomedical-cr", 0.76,
     "Nanomedical Costa Rica designs targeted nanoparticle delivery systems for diagnostic imaging contrast agents and clinical detection applications. Its primary technology is nano-engineered diagnostic probes for medical imaging — detection and diagnosis, not therapeutic treatment."),

    # future_cow + updairy: precision fermentation food products
    ("future_cow", 0.80,
     "Future Cow uses precision fermentation to produce dairy-identical milk proteins — casein and whey — without animals. Its end product is a food ingredient for dairy alternative products consumed by humans, placing it squarely in Food Systems and alternative proteins."),

    ("updairy", 0.80,
     "UpDairy applies precision fermentation to produce animal-free whey and casein proteins for use in dairy-alternative food products. Its commercial output is a food ingredient — protein for human consumption — not a biomanufacturing platform service."),

    # radbio: radiation biology diagnostics vs therapeutics
    ("radbio", 0.77,
     "RadBio develops radiation-responsive molecular diagnostic biomarkers for real-time clinical assessment of radiation exposure and radiotherapy treatment response in oncology patients. Its technology is a diagnostic monitoring tool for clinical decision-making, not a therapeutic intervention."),

    # qnity: diagnostics company
    ("qnity", 0.78,
     "Qnity develops point-of-care biosensors and rapid diagnostic devices for metabolic and infectious disease detection in low-resource clinical settings. Its product is a diagnostic measurement device — test strips, readers, assays — not a therapeutic treatment."),

    # kheiron: bioinput angle very explicit
    ("kheiron-biotech-ar", 0.79,
     "Kheiron Biotech applies somatic cell nuclear transfer and reproductive cloning technology to produce genetically elite bovine and equine embryos for sale to breeders. Its commercial output is biological reproductive material — embryos and germplasm — that functions as a genetic bioinput into livestock breeding programs. No veterinary treatment or pharmaceutical product is developed."),

    # bioseek: diagnostics, not therapeutics
    ("bioseek", 0.77,
     "Bioseek develops AI-powered digital pathology platforms and molecular diagnostic assays for early detection of oncological and infectious conditions. Its product is a diagnostic screening tool — software and assay kits — not a therapeutic drug or treatment."),
]

for sid, conf, summary in summary_fixes:
    rows.append([sid, "startup_extended", "startup_summary_en", summary,
                 src, conf, f"summary_rewrite_wave3_2026-06-26"])

with open(out, "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    for r in rows:
        w.writerow(r)

print(f"Written {len(rows)} rows")
print(f"  Reclassifications: {len(reclassify)}")
print(f"  Summary rewrites: {len(summary_fixes)}")
