"""
src/reclassify.py — BIO Editorial Category classifier (v3 — clean).

7 editorial categories derived bottom-up from semantic clusters:
  1. Farm Intelligence
  2. Bioinputs & Crop Resilience
  3. Food Systems & Alt Proteins
  4. Biomaterials & Circular Economy
  5. Nature & Ecosystem Tech
  6. Diagnostics & Health Access
  7. Therapeutics

PRIMARY SIGNAL: keyword scoring on startup_summary_en (English-normalized).
No cluster bypass. Clusters are visual only — classification is stable and
deterministic, independent of HDBSCAN runs.

Disambiguation principle for edge cases:
  Food Systems  = fermentation/biology whose OUTPUT goes into food/nutrition
  Biomaterials  = fermentation/biology whose OUTPUT is a material/chemical/energy

Usage:
    python pipeline.py reclassify-themes
    python pipeline.py reclassify-themes --dry-run
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

from src.audit import diff_and_log_update

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "db" / "bio_latam.db"


# ──────────────────────────────────────────────────────────────────────────────
# 7 EDITORIAL THEMES
# Keyword weights tuned so output-destination (food vs material vs therapeutic)
# dominates over biological mechanism (fermentation, protein, microorganism).
# ──────────────────────────────────────────────────────────────────────────────

THEMES: dict[str, dict] = {

    "Farm Intelligence": {
        "description": (
            "Digital intelligence for agriculture: precision farming platforms, agronomic "
            "decision tools, satellite/drone monitoring, IoT crop sensors, agrifintech, "
            "and farm management software."
        ),
        "domains":        {"agri-food": 0.8},
        "lens":           {},
        "industry_codes": {"precision_ag": 2.5, "agtech": 1.0, "agrifintech": 2.5,
                           "farm_management": 2.0},
        "tech_codes":     {"remote_sensing": 2.0, "satellite": 2.0, "iot": 0.8},
        "keywords": {
            r"precision.agr": 2.5, r"precision.farm": 2.5,
            r"agronomic.decision": 2.5, r"agronomic.recommend": 2.5,
            r"agron.*platform": 2.0, r"farm.management": 2.0,
            r"crop.analytic": 2.5, r"crop.monitor": 2.0,
            r"satellite.imager": 2.0, r"georeferenced": 2.0,
            r"multispectral": 1.5, r"drone.*agr": 1.5,
            r"precision.irrigation": 2.0, r"smart.irrigation": 2.0,
            r"iot.*crop": 1.5, r"resource.intelligence": 2.5,
            r"agrifintech": 3.0, r"rural.credit": 2.5, r"rural.finance": 2.5,
            r"farm.loan": 2.5, r"agricultural.credit": 2.5,
            r"crop.insurance": 2.0, r"smart.farming": 2.0, r"digital.farm": 2.0,
            r"agronomic.data": 2.5, r"agronomic.efficiency": 2.5,
            r"agtech": 1.5, r"agrotech": 1.5,
            r"ai.*agron": 2.0, r"virtual.field": 2.0,
            r"traceabilit.*agr": 1.5,
        },
        "is_bio_default": False,
    },

    "Bioinputs & Crop Resilience": {
        "description": (
            "Biological inputs for agriculture and biological interventions in crop/plant "
            "systems: biofertilizers, biostimulants, biopesticides, biocontrol agents, "
            "CRISPR/gene-edited crop varieties, precision breeding, seed treatments, "
            "plant tissue culture, entomopathogenic solutions."
        ),
        "domains":        {"agri-food": 1.5},
        "lens":           {"biocentric": 1.0, "regenerative": 0.8, "biobased": 0.5},
        "industry_codes": {"bioinputs": 3.0, "soil_health": 2.0, "seeds": 2.0,
                           "crop_protection": 2.0},
        "tech_codes":     {"gene_editing": 3.0, "genomics": 0.5},
        "keywords": {
            r"bioinput": 2.5, r"biofertili": 2.5, r"bioestimul": 2.5,
            r"biostimul": 2.5, r"inoculant": 2.5, r"nitrogen.fix": 2.5,
            r"rhizob": 2.5, r"mycorrhiz": 2.5, r"pgpr": 2.5,
            r"soil.microb": 2.5, r"soil.health": 1.5, r"rhizosphere": 2.5,
            r"biological.input": 2.5, r"biological.crop": 2.0,
            r"biological.nitrogen": 2.5, r"plant.growth.promot": 2.5,
            r"azotobacter": 2.5, r"azospirill": 2.5,
            r"biopesticide": 3.0, r"bio.pesticide": 3.0, r"biocontrol": 2.5,
            r"tick": 2.0, r"entomopathogen": 3.0, r"beauveria": 3.0,
            r"metarhizium": 3.0, r"fungal.based.*pest": 2.5,
            r"pest.control.*bio": 2.0, r"biological.*pest": 2.0,
            r"bioinsecticide": 3.0, r"biofungi": 3.0, r"biofungicide": 3.0,
            r"crispr.*crop": 3.0, r"gene.edit.*crop": 3.0, r"gene.edit.*plant": 3.0,
            r"precision.breed": 2.5, r"transgenic": 2.0,
            r"plant.breed": 2.0, r"seed.treatment": 2.5, r"seed.biotech": 2.5,
            r"soybean.rust": 2.5, r"asian.rust": 2.5, r"herbicide.resist": 2.0,
            r"plant.pathog": 2.0, r"crop.resilience": 2.5, r"crop.protect": 2.0,
            r"tissue.cultur": 2.5, r"plant.tissue": 2.5, r"biofactori.*plant": 2.0,
            r"post.harvest": 2.5, r"shelf.life.*fruit": 2.5, r"fruit.preserv": 2.0,
            r"gradual.release.*fertili": 2.5, r"organic.mineral.fertili": 2.5,
            r"rna.pesticide": 2.5, r"antisense.rna.*plant": 2.5,
        },
        "is_bio_default": True,
    },

    "Food Systems & Alt Proteins": {
        "description": (
            "Companies whose OUTPUT goes into human or animal food/nutrition: precision "
            "fermentation for food proteins/dairy/fats, novel food ingredients, "
            "functional foods, nutraceuticals, prebiotics/probiotics (food context), "
            "plant-based food products, cultivated/cell-based meat, insect protein, "
            "aquaculture biotech, and food biopreservation."
            "\n"
            "Key distinction from Biomaterials: the END PRODUCT is ingested (food, "
            "supplement, ingredient) — not a material, packaging, or industrial chemical."
        ),
        "domains":        {"agri-food": 1.0, "biomanufacturing": 0.3},
        "lens":           {"biobased": 0.5},
        "industry_codes": {"alternative_protein": 3.0, "novel_foods": 2.5,
                           "aquaculture": 2.0, "seafood": 1.5,
                           "food_ingredients": 2.5, "foodtech": 1.5},
        "tech_codes":     {"fermentation": 0.8, "cellular_ag": 3.0},
        "keywords": {
            # food-destination fermentation (output = food/ingredient)
            r"precision.ferment.*protein": 3.0, r"precision.ferment.*food": 3.0,
            r"precision.ferment.*dairy": 3.0, r"precision.ferment.*milk": 3.0,
            r"precision.ferment.*ingredient": 3.0,
            r"ferment.*dairy": 2.5, r"ferment.*food": 2.5,
            r"ferment.*ingredient": 2.5, r"ferment.*aliment": 2.5,
            r"ferment.*milk": 2.5, r"ferment.*protein.*food": 3.0,
            # dairy & dairy alternatives (always food)
            r"dairy.alt": 3.0, r"animal.free.dairy": 3.0,
            r"plant.based.dairy": 3.0, r"dairy.alternative": 3.0,
            r"cheese\b": 2.5, r"milk.alternative": 2.5, r"oat.milk": 2.5,
            r"casein.*food": 2.5, r"whey.protein.*food": 2.5,
            r"lactoferrin.*food": 2.5, r"breastmilk": 3.0, r"infant.nutrition": 3.0,
            # nutraceuticals / functional food
            r"nutraceutical": 2.5, r"functional.food": 2.5,
            r"functional.ingredient": 2.5, r"food.ingredient": 2.5,
            r"bioactive.*food": 2.5, r"healthspan": 2.0,
            r"prebiotic": 2.5, r"probiotic.*food": 2.0, r"probiotic.*gut": 2.0,
            r"microbiome.*food": 2.0, r"gut.health": 2.0,
            # natural pigments / colorants in food context
            r"astaxanthin": 2.5, r"carotenoid.*food": 2.5, r"natural.colorant": 2.5,
            r"natural.pigment.*food": 2.5,
            # novel food ingredients
            r"novel.ingredient": 3.0, r"novel.food": 2.5,
            r"foodtech": 2.0, r"aliment": 1.5, r"food.biotech": 2.5,
            # alt protein
            r"cultivated.meat": 3.0, r"cell.based.meat": 3.0, r"cultured.meat": 3.0,
            r"cell.cultivated": 2.5, r"scaffold.*meat": 2.5,
            r"plant.based.protein": 2.5, r"plant.based.meat": 2.5,
            r"plant.based.food": 2.5, r"plant.based.ingredient": 2.5,
            r"alternative.protein": 2.5, r"novel.protein": 2.0,
            r"insect.protein": 3.0, r"black.soldier.fly": 3.0, r"bsf\b": 2.0,
            r"mycoprotein": 3.0, r"fungal.protein.*food": 2.5,
            r"microalgae.protein": 2.5, r"algae.*food": 2.0, r"algae.*ingredient": 2.5,
            r"duckweed": 3.0, r"lemna": 3.0,
            r"vegan.food": 2.0, r"animal.free.food": 2.0,
            # aquaculture / seafood
            r"aquaculture": 2.5, r"sustainable.shrimp": 2.5,
            r"totoaba": 3.0, r"huachinango": 3.0, r"fish.protein": 2.5,
            # food preservation / shelf life (food context)
            r"shelf.life.*food": 2.5, r"food.preserv": 2.5, r"biopreserv.*food": 2.5,
            r"extend.*shelf.*food": 2.5, r"bio.preserv": 2.5,
            # antibiotics for aquaculture / animal feed
            r"probiotic.*feed": 2.0, r"animal.feed.*bio": 1.5,
            r"salmon.*bioact": 2.0, r"fish.bioact": 2.0,
        },
        "is_bio_default": True,
    },

    "Biomaterials & Circular Economy": {
        "description": (
            "Companies using biological processes to produce materials, chemicals, or "
            "energy carriers replacing petrochemical equivalents. The OUTPUT is a "
            "material, industrial chemical, or energy product — not food.\n"
            "Covers bioplastics, biopolymers, mycelium materials, biobased packaging, "
            "industrial enzymes (non-food), green chemistry, e-fuels, biogas for energy."
        ),
        "domains":        {"biomanufacturing": 2.0, "industrial-biotech": 3.0,
                           "biomaterials": 2.5},
        "lens":           {"biobased": 1.5, "bio-enabled-industrial-transition": 2.0,
                           "circular": 1.0},
        "industry_codes": {"biomaterials": 2.5, "bioplastics": 3.0, "industrial_bio": 2.5,
                           "enzymes": 2.0, "materials_packaging": 1.0},
        "tech_codes":     {"synbio": 2.0, "green_chem": 2.5, "biomaterials": 2.5},
        "keywords": {
            # materials output (explicit)
            r"biomaterial": 3.0, r"biobased.chemi": 3.0, r"bio.based.chemi": 3.0,
            r"bioplastic": 3.0, r"biopolymer": 3.0, r"bioresin": 3.0,
            r"mycelium.*material": 3.0, r"mycelium.*packag": 3.0,
            r"fungal.material": 2.5, r"filamentous.fungi.*material": 2.5,
            # industrial enzymes (non-food application)
            r"industrial.enzyme": 2.5, r"enzyme.platform": 2.5,
            r"enzymatic.*industrial": 2.5, r"enzyme.*textile": 2.5,
            r"enzyme.*detergent": 2.5, r"enzyme.*pulp": 2.5,
            # packaging & circular
            r"biobased.packaging": 3.0, r"biodegradable.packaging": 3.0,
            r"compostable.packag": 2.5, r"plant.based.packaging": 2.5,
            r"sustainable.packaging.*material": 2.0,
            r"circular.bioeconomy": 2.5, r"biomateriales": 3.0,
            # industrial biotech / biomanufacturing (non-food)
            r"biobased\b.*material": 2.5, r"bio.based.*material": 2.5,
            r"bio.based.*chemical": 2.5, r"biobased.*chemical": 2.5,
            r"green.chemi": 2.5, r"green.chemistry": 2.5,
            r"industrial.biotech": 2.5, r"industrial.biotechnology": 2.5,
            r"biobased.solvent": 2.5, r"bio.based.solvent": 2.5,
            r"synth.bio.*material": 2.5, r"synthetic.biology.*material": 2.5,
            # fermentation for materials (explicit material output)
            r"ferment.*bioplastic": 3.0, r"ferment.*biomaterial": 3.0,
            r"ferment.*polymer": 2.5, r"ferment.*packaging": 2.5,
            r"precision.ferment.*material": 2.5, r"precision.ferment.*chemical": 2.5,
            # e-fuels / synthetic energy
            r"e.fuel": 3.0, r"efuel": 3.0, r"e-fuel": 3.0,
            r"synthetic.fuel": 3.0, r"electrofuel": 3.0,
            r"carbon.neutral.fuel": 3.0, r"green.hydrogen": 2.5, r"green.ammonia": 2.5,
            r"biogas.*energy": 2.0, r"biogas.*power": 2.0,
        },
        "is_bio_default": True,
    },

    "Nature & Ecosystem Tech": {
        "description": (
            "Companies applying technology to protect, restore, or monitor natural "
            "ecosystems: carbon removal/sequestration, reforestation tech, biodiversity "
            "monitoring, ocean/aquatic ecosystem health, bioremediation, water quality, "
            "satellite forest monitoring, and ecosystem service markets."
        ),
        "domains":        {"biodiversity-nature": 3.0, "climate-resource": 0.8},
        "lens":           {"planetary-boundary": 1.0, "regenerative": 0.5},
        "industry_codes": {"carbon": 2.5, "biodiversity": 3.0, "water": 1.5,
                           "ocean": 2.5, "bioremediation": 3.0, "reforestation": 3.0},
        "tech_codes":     {"remote_sensing": 1.0},
        "keywords": {
            r"carbon.remov": 3.0, r"carbon.sequester": 3.0, r"carbon.credit": 2.5,
            r"reforestation": 3.0, r"amazon.reforest": 3.0, r"native.forest": 2.5,
            r"biodiversit": 3.0, r"nature.based.solution": 3.0,
            r"planetary.boundar": 3.0, r"ecosystem.service": 2.5,
            r"ecosystem.monitor": 2.5, r"ecosystem.restor": 2.5,
            r"forest.monitor": 2.5, r"forest.certification": 2.5,
            r"deforestation": 2.5, r"land.use": 2.0,
            r"satellite.*forest": 2.5, r"satellite.*biodiv": 2.5,
            r"ocean.farm": 2.5, r"marine.biotech.*env": 2.5,
            r"nanobubble": 2.5, r"water.quality": 2.0,
            r"bioremedi": 3.0, r"environmental.remediat": 2.5,
            r"kelp": 2.5, r"seaweed.*env": 2.0, r"microalgae.*env": 2.0,
            r"pollinator": 2.5, r"bee.health": 2.5,
            r"soil.carbon.*climate": 2.0, r"regenerative.agr.*carbon": 2.0,
            r"bioleach": 3.0, r"mine.remediat": 2.5,
            r"nature.finance": 2.5, r"conservation.finance": 2.5,
            r"biodiversity.credit": 2.5, r"nature.asset": 2.5,
        },
        "is_bio_default": True,
    },

    "Diagnostics & Health Access": {
        "description": (
            "Companies applying biology to detect, monitor, or measure human disease. "
            "Includes molecular diagnostics, point-of-care testing, biosensors, "
            "medical devices with biological components, fertility diagnostics, "
            "spectral/imaging diagnostics, and digital health platforms where a "
            "biological assay is the core component."
        ),
        "domains":        {"diagnostics-medtech": 3.0, "human-health": 0.8},
        "lens":           {"human-health-bio": 1.5},
        "industry_codes": {"diagnostics": 3.0, "medtech": 2.5, "fertility": 2.5,
                           "point_of_care": 3.0, "human_health": 0.5},
        "tech_codes":     {"diagnostics": 3.0, "biosensor": 3.0, "lateral_flow": 3.0,
                           "microfluidics": 2.5, "digital_pathology": 2.0},
        "keywords": {
            r"diagnostic": 2.5, r"diagnostico": 2.0,
            r"point.of.care": 3.0, r"poc.test": 3.0,
            r"lateral.flow": 3.0, r"biosensor": 3.0,
            r"biomarker.detect": 2.5, r"molecular.test": 2.5,
            r"molecular.diagnos": 2.5, r"microfluidic": 2.5, r"lab.on.chip": 2.5,
            r"circulating.tumor": 3.0, r"liquid.biopsy": 3.0,
            r"fertility.diagnos": 2.5, r"ivf.*diagnos": 2.5,
            r"tuberculosis.test": 2.5, r"dengue.test": 2.5,
            r"infectious.disease.detect": 2.5, r"rapid.test": 2.5,
            r"rapid.diagnos": 2.5, r"crispr.*diagnos": 2.5,
            r"sterilization.indicator": 2.0,
            r"intracranial.pressure": 2.5,
            r"breast.cancer.screen": 2.5,
            r"blood.viscosity": 2.5, r"hematology": 2.0,
            r"laparoscop": 2.5, r"minimally.invasive.*device": 2.5,
            r"surgical.magnet": 3.0, r"organ.retract": 2.5,
            r"medtech": 1.5, r"medical.device": 2.0,
            r"spectral.fingerprint": 3.0, r"fingerprint.*diagnos": 2.5,
            r"smart.spectral": 2.5, r"nir.*food.*quality": 2.0,
            r"genomic.*diagnos": 2.5, r"genetic.test": 2.0,
            r"digital.patholog": 3.0, r"pathology.ai": 2.5,
            r"speech.*detect": 2.0, r"speech.*diagnos": 2.0,
            r"corneal.*diagnos": 2.5, r"ophthalm.*diagnos": 2.5,
            r"non.invasive.*diagnos": 2.0, r"non.invasive.*monitor.*health": 2.0,
            r"cognitive.*diagnos": 2.0, r"neurocognitive.*test": 2.5,
            r"ultrafiltration.*diagnos": 1.5,
        },
        "is_bio_default": True,
    },

    "Therapeutics": {
        "description": (
            "Companies developing treatments that intervene in human or animal biology "
            "to cure, manage, or prevent disease: drug discovery, biologics, monoclonal "
            "antibodies, biosimilars, cell/gene therapy, mRNA therapeutics, oncology, "
            "rare diseases, regenerative medicine, nanomedicine, veterinary therapeutics, "
            "and drug delivery systems."
        ),
        "domains":        {"therapeutics-regenerative": 3.5, "human-health": 0.6},
        "lens":           {"human-health-bio": 1.5},
        "industry_codes": {"therapeutics": 3.0, "oncology": 3.0, "rare_disease": 3.0,
                           "biologics": 3.0, "biosimilars": 3.0, "animal_health": 1.5,
                           "regenerative_medicine": 3.0},
        "tech_codes":     {"drug_discovery": 3.0, "cell_therapy": 3.0,
                           "gene_therapy": 3.0, "mrna": 3.0, "antibody": 2.5},
        "keywords": {
            r"drug.discover": 3.0, r"drug.candidate": 3.0,
            r"clinical.trial": 3.0, r"phase.[123i]": 3.0,
            r"monoclonal.antibod": 3.0, r"biosimilar": 3.0,
            r"biopharmaceut": 2.5, r"biologic.drug": 3.0,
            r"cell.therap": 3.0, r"gene.therap": 3.0,
            r"mrna.vaccine": 3.0, r"mrna.therap": 3.0,
            r"oncolytic": 3.0, r"oncolog": 2.0,
            r"tumor.treat": 2.5, r"cancer.treat": 2.5, r"cancer.therap": 2.5,
            r"rare.disease": 3.0, r"hemolytic": 3.0,
            r"immunotherap": 2.5, r"immune.checkpoint": 2.5,
            r"regenerative.medicine": 2.5, r"regenerative.med": 2.5,
            r"tissue.engineer": 2.5, r"stem.cell.therap": 2.5,
            r"exosome.therap": 2.5, r"nanomedicin": 2.5,
            r"peptide.therap": 2.5, r"bioactive.peptide.*therap": 2.0,
            r"veterinary.drug": 2.0, r"animal.vaccine": 2.0, r"mastitis": 2.0,
            r"rna.therap": 3.0, r"mirna.therap": 3.0, r"antisense.oligo": 3.0,
            r"neurodegenerative": 2.5, r"sodium.channel.block": 3.0,
            r"bioprint.*tissue": 3.0, r"3d.bioprint": 3.0, r"organ.on.chip": 2.5,
            r"drug.deliver": 2.5, r"nanoparticle.*drug": 2.5,
            r"lipid.nanoparticle.*drug": 2.5, r"lipid.nanoparticle.*therap": 2.5,
            r"ophthalmic.*drug": 2.5, r"intravitreal": 3.0,
            r"dermal.filler": 2.5, r"joint.injection": 2.5,
            r"cattle.health.*therap": 2.0, r"livestock.therap": 2.0,
            r"animal.cloning": 2.5,
            r"terapia": 2.0, r"terapias": 2.0, r"therapeutics": 1.5,
            r"wound.heal.*therap": 2.5, r"wound.care": 2.0,
            r"galectin": 2.5, r"tgf.beta": 2.5, r"immunomodul": 2.5,
            r"protein.engineer.*therap": 2.5, r"de.novo.*protein.*therap": 2.5,
            r"protein.function.*therap": 2.0,
            # Animal reproduction as therapeutic intervention
            r"animal.reproduct.*biotechn": 2.0, r"embryo.transfer": 2.5,
            r"bovine.reproduct": 2.5, r"in.vitro.fertiliz": 2.0,
        },
        "is_bio_default": True,
    },
}

THEME_NAMES = list(THEMES.keys())

# Signals that mark eco-adjacent / non-bio-core companies
NON_BIO_SIGNALS = [
    r"agrifintech", r"agri.fintech", r"agro.crédito", r"agrocredito",
    r"farm.management.software", r"ehr.system", r"telemedicine.platform",
    r"crop.insurance.digital", r"grain.trading.platform", r"commodity.trading",
    r"logistics.platform", r"supply.chain.software", r"marketplace.agr",
    r"digital.bank.agr", r"agricultural.credit", r"farm.loan",
    r"scheduling.health", r"electronic.health.record",
]

NON_BIO_DOMAINS = {"fintech", "logistics", "edtech", "legaltech"}


# ──────────────────────────────────────────────────────────────────────────────
# Scoring engine
# ──────────────────────────────────────────────────────────────────────────────

def _parse_tags(raw: str | None) -> set[str]:
    if not raw:
        return set()
    return {t.strip().lower() for t in re.split(r"[;,]", raw) if t.strip()}


def _parse_json_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        return [str(x).lower() for x in json.loads(raw)]
    except Exception:
        return []


def score_startup(row: dict) -> dict[str, float]:
    """Return {theme: score} for a startup. Uses English summary preferentially."""
    scores = {t: 0.0 for t in THEME_NAMES}

    domains  = _parse_tags(row.get("domain_tags"))
    lens     = _parse_tags(row.get("bio_lens_tags"))
    tech_c   = _parse_json_list(row.get("tech_codes"))
    ind_c    = _parse_json_list(row.get("industry_codes"))

    # English summary preferred — regex patterns are in English
    summary = (
        row.get("startup_summary_en")
        or row.get("startup_summary_v1")
        or row.get("short_description")
        or ""
    ).lower()

    for theme, td in THEMES.items():
        s = 0.0
        for d, w in td["domains"].items():
            if d in domains:
                s += w
        for tag, w in td["lens"].items():
            if tag in lens:
                s += w
        for code, w in td["industry_codes"].items():
            if any(code in ic for ic in ind_c):
                s += w
        for code, w in td["tech_codes"].items():
            if any(code in tc for tc in tech_c):
                s += w
        for pattern, w in td["keywords"].items():
            if re.search(pattern, summary):
                s += w
        scores[theme] = s

    return scores


def classify(scores: dict[str, float]) -> tuple[str | None, str | None, float]:
    """Return (primary, secondary, confidence)."""
    ranked = sorted(scores.items(), key=lambda x: -x[1])
    if not ranked or ranked[0][1] == 0:
        return None, None, 0.0

    primary_name, primary_score = ranked[0]
    second_name, second_score   = ranked[1] if len(ranked) > 1 else (None, 0.0)

    secondary = None
    if second_score >= 0.40 * primary_score and second_score > 1.5:
        secondary = second_name

    total = primary_score + second_score if second_score else primary_score
    confidence = round(primary_score / total, 3) if total else 0.0
    return primary_name, secondary, confidence


def is_bio(row: dict, primary: str | None, scores: dict[str, float]) -> int:
    """Return 1 if bio-core, 0 if eco-adjacent."""
    if primary is None:
        return 0

    summary = (
        row.get("startup_summary_en")
        or row.get("startup_summary_v1")
        or row.get("short_description")
        or ""
    ).lower()
    lens = _parse_tags(row.get("bio_lens_tags"))

    strong_bio_lens = {"biobased", "human-health-bio", "bio-enabled-industrial-transition"}
    if strong_bio_lens & lens:
        return 1

    for pattern in NON_BIO_SIGNALS:
        if re.search(pattern, summary):
            return 0

    domains = _parse_tags(row.get("domain_tags"))
    if domains & NON_BIO_DOMAINS and not (lens & {"biocentric", "biobased"}):
        return 0

    theme_def = THEMES.get(primary, {})
    if theme_def.get("is_bio_default", True):
        if scores.get(primary, 0.0) < 1.5:
            return 1 if ("biocentric" in lens) else 0
        return 1

    return 0


# ──────────────────────────────────────────────────────────────────────────────
# DB layer
# ──────────────────────────────────────────────────────────────────────────────

def load_startups(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT
            sx.startup_id,
            e.canonical_name,
            e.short_description,
            e.country_code,
            sx.startup_summary_en,
            sx.startup_summary_v1,
            sx.business_one_liner,
            sx.bio_lens_tags,
            sx.domain_tags,
            sx.technology_tags,
            sx.tech_codes,
            sx.industry_codes,
            sx.macro_theme,
            sx.scope_basis
        FROM startup_extended sx
        JOIN entities e ON e.entity_id = sx.startup_id
        WHERE sx.scope_decision = 'include'
        ORDER BY e.canonical_name
    """).fetchall()
    conn.row_factory = None
    return [dict(r) for r in rows]


def run(db_path: Path = DB_PATH, dry_run: bool = False) -> tuple[dict, list[dict]]:
    conn = sqlite3.connect(db_path)
    startups = load_startups(conn)

    results: list[dict] = []
    theme_counts: dict[str, int] = {t: 0 for t in THEME_NAMES}
    bio_count = 0
    non_bio_count = 0
    unclassified = 0

    for row in startups:
        sid = row["startup_id"]
        scores = score_startup(row)
        primary, secondary, confidence = classify(scores)
        bio_flag = is_bio(row, primary, scores)

        if primary is None:
            unclassified += 1

        results.append({
            "startup_id": sid,
            "name":       row["canonical_name"],
            "primary":    primary,
            "secondary":  secondary,
            "confidence": confidence,
            "is_bio":     bio_flag,
            "top_scores": {t: round(s, 2) for t, s in
                           sorted(scores.items(), key=lambda x: -x[1])[:3]},
        })

        if primary:
            theme_counts[primary] = theme_counts.get(primary, 0) + 1
        if bio_flag:
            bio_count += 1
        else:
            non_bio_count += 1

    if not dry_run:
        updated = 0
        for r in results:
            n = diff_and_log_update(
                conn, "startup_extended", "startup_id", r["startup_id"],
                {
                    "bio_theme_primary":    r["primary"],
                    "bio_theme_secondary":  r["secondary"],
                    "is_bio_universe":      r["is_bio"],
                    "bio_theme_confidence": r["confidence"],
                },
                actor="pipeline:reclassify",
                reason=(
                    f"keyword_scorer_v3 | primary={r['primary']} "
                    f"conf={r['confidence']:.2f}"
                ),
            )
            updated += n
        conn.commit()
        print(f"\n  Updated {updated} rows in startup_extended")

    conn.close()

    stats = {
        "total":        len(results),
        "bio_core":     bio_count,
        "eco_adjacent": non_bio_count,
        "unclassified": unclassified,
        "by_theme":     {k: v for k, v in
                         sorted(theme_counts.items(), key=lambda x: -x[1])},
    }
    return stats, results
