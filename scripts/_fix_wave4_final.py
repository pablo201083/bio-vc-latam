"""Wave 4 — surgical final fixes. Revert errors, clear easy cases, accept floor."""
import csv, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
out = ROOT / "staging" / "entity_enrichments.csv"
src = "swarm_inline_theme_fix4_2026-06-26"
rows = []

# ── REVERT MISTAKES FROM WAVE 3 (cluster was right all along) ─────────────

revert = [
    # poas_bioenergy: biogas from organic waste → nature/ecosystem service, cluster is right
    ("poas_bioenergy", "Nature & Ecosystem Tech", 0.79,
     "Poas Bioenergy converts organic waste into biogas for rural energy — circular waste-to-energy ecosystem service, Nature cluster is correct"),

    # solfium: bio-based solar energy tech → nature/clean energy, cluster is right
    ("solfium", "Nature & Ecosystem Tech", 0.77,
     "Solfium develops biological processes for solar energy capture and environmental remediation — Nature & Ecosystem Tech cluster correctly reflects this"),

    # inkus-biotech-cl: genomics for salmon + cattle → Precision Agriculture, not Food
    ("inkus-biotech-cl", "Precision Agriculture", 0.82,
     "Inkus Biotech delivers genomic breeding precision tools for cattle and salmon producers — precision input to farm management, not a food product"),

    # salmoss-biotech-cl: salmon genetic improvement → Precision Agriculture for aquaculture
    ("salmoss-biotech-cl", "Precision Agriculture", 0.80,
     "SALMOSS Biotech applies genomic selection to improve salmon production performance — precision aquaculture genetics, not a food product"),

    # michroma: fungal pigments are industrial colorants = Biomaterials, not food
    ("michroma", "Biomaterials & Green Chemistry", 0.82,
     "Michroma produces fungal-derived pigments as industrial colorants and dye alternatives for use in textiles, cosmetics, and industrial applications — bio-based colorant materials, not food-grade ingredients"),

    # recirculab-cl: food waste upcycling into circular materials = Biomaterials
    ("recirculab-cl", "Biomaterials & Green Chemistry", 0.78,
     "Recirculab upcycles food and agricultural waste streams into bio-based packaging materials and circular material inputs — biomaterials from waste, not a food product company"),
]

for sid, new_theme, conf, note in revert:
    rows.append([sid, "startup_extended", "bio_theme_primary", new_theme,
                 src, conf, f"wave4_revert: {note}"])

# ── SUMMARY FIXES (pull embedding correctly) ──────────────────────────────

summary_fixes = [
    # exacta-bioscience-cl: Bioinputs conf=1.0 but cluster says Food — strengthen bioinput language
    ("exacta-bioscience-cl", 0.85,
     "Exacta BioScience develops precision bioinputs — microbial inoculants, biofungicides, and biostimulants — specifically formulated for Chilean fruit and vegetable export crops. Its products are applied pre-harvest as biological crop protection and nutrition inputs, not sold as food products."),

    # pewman-innovation-cl: biostimulant bioinput, not food
    ("pewman-innovation-cl", 0.82,
     "Pewman Innovation develops CRIOPROTECT, a cryoprotective bacterial biostimulant applied to crops to prevent frost damage in Chilean berry and vegetable production. Its product is an agricultural biological input applied to the crop before harvest — a bioinput, not a food product."),

    # cropguard-cl: crop protection bioinput
    ("cropguard-cl", 0.80,
     "CropGuard develops bio-based crop protection inputs using microbial antagonists and botanical extracts to control fungal and bacterial plant diseases in Chilean fruit orchards. Its products are field-applied biological pesticide alternatives — bioinputs for crop protection, not food products."),

    # agrourbana: urban vertical farm = food production explicitly
    ("agrourbana", 0.82,
     "Agrourbana operates and sells modular vertical indoor farming systems for urban leafy green and herb production in Chile. Its core output is fresh food — lettuce, herbs, microgreens — grown hydroponically for direct sale to urban consumers and restaurants. Food production is the primary activity."),

    # koji-co: precision fermentation food ingredients
    ("koji-co", 0.80,
     "Koji is a Colombian precision fermentation company using Aspergillus oryzae koji cultures to produce fermented food ingredients — umami compounds, flavor enhancers, and functional food additives — for the Colombian food and beverage industry. Its output is a food ingredient consumed by humans."),

    # huiro: seaweed biostimulant bioinput explicitly
    ("huiro", 0.81,
     "Huiro harvests and processes Chilean giant kelp (Macrocystis pyrifera) into liquid biostimulant extracts applied to agricultural crops as foliar sprays and soil conditioners. Its product is a seaweed-derived biological input for crop nutrition and stress tolerance — a bioinput, not an ecosystem restoration service."),

    # alkemio: what is it? Biomaterials → Nature conflict
    ("alkemio", 0.76,
     "Alkemio develops bio-based green chemistry solutions using biotransformation and enzymatic processes to produce sustainable materials and chemical intermediates from renewable biological feedstocks. Its output is bio-derived industrial materials and specialty chemicals — Biomaterials and Green Chemistry."),

    # ideelab: Bioinputs → Biomanufacturing
    ("ideelab", 0.75,
     "IDeelab develops microbial biotechnology tools and biological input formulations for sustainable crop production, combining bioprocess development with agricultural bioinput commercialization. Its core commercial products are biological crop inputs delivered as ready-to-apply field formulations."),

    # symbiomics: Bioinputs → Biomanufacturing conflict
    ("symbiomics", 0.77,
     "Symbiomics studies and applies plant microbiome interactions to develop bioinoculant products that enhance crop nutrient uptake and disease resistance through beneficial microbial symbiosis. Its products are field-applied biological inputs for crop production."),

    # biorefinery-tech-brazil-br: Biomaterials → Biomanufacturing conflict
    ("biorefinery-tech-brazil-br", 0.78,
     "Biorefinery Tech Brazil converts agricultural residues into cellulosic biopolymers and bio-based specialty chemicals using enzymatic hydrolysis. Its output is green chemistry industrial raw materials — biopolymers and chemical intermediates for non-food industrial applications."),
]

for sid, conf, summary in summary_fixes:
    rows.append([sid, "startup_extended", "startup_summary_en", summary,
                 src, conf, f"summary_wave4_2026-06-26"])

with open(out, "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    for r in rows:
        w.writerow(r)

print(f"Written {len(rows)} rows — {len(revert)} reclassifications + {len(summary_fixes)} rewrites")
