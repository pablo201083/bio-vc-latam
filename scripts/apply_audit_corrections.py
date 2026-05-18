"""
scripts/apply_audit_corrections.py

Aplica las correcciones de la auditoría crítica de clusters y temas (2026-05-18).
Agrega filas a staging/entity_enrichments.csv.
"""
import csv
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "staging" / "entity_enrichments.csv"
SOURCE = "internal:audit-cluster-theme-review-2026-05-18"

NEW_ROWS = [
    # ── bio_theme_primary corrections ─────────────────────────────────────
    ("dharma_bioscience", "Dharma BioScience", "startup_extended", "bio_theme_primary",
     "Therapeutics", SOURCE, "0.92",
     "Regenerative medicine (tissue regen). cluster_id=7 Therapeutics already correct. theme Diagnostics was error (conf=0.52)."),

    ("inner_cosmos", "Inner Cosmos", "startup_extended", "bio_theme_primary",
     "Therapeutics", SOURCE, "0.90",
     "Implantable BCI for treatment-resistant depression — therapeutic device, not diagnostic. bio_theme_conf was 0.60."),

    ("beeflow", "Beeflow", "startup_extended", "bio_theme_primary",
     "Bioinputs & Crop Resilience", SOURCE, "0.88",
     "Pollination-as-a-service + bee nutrition biologicals = ag biological input. macro_theme=ag biologicals confirms."),

    ("agrired", "Agrired", "startup_extended", "bio_theme_primary",
     "Farm Intelligence", SOURCE, "0.87",
     "B2B marketplace for agro inputs — distributes, does not develop bioinputs. Bioinputs reserved for developers."),

    ("kigui", "Kigui", "startup_extended", "bio_theme_primary",
     "Food Systems & Alt Proteins", SOURCE, "0.85",
     "Retail AI for food expiration/waste reduction. Food Systems, not Nature/Ecosystem. secondary was already Food Systems."),

    ("agrotoken", "Agrotoken", "startup_extended", "bio_theme_primary",
     "Farm Intelligence", SOURCE, "0.82",
     "Blockchain tokenization of grains = agri-digital infrastructure. bio_theme_conf=0.55 confirms low certainty in Nature/Ecosystem."),

    ("phagelab", "PhageLab", "startup_extended", "bio_theme_primary",
     "Bioinputs & Crop Resilience", SOURCE, "0.90",
     "Animal health phage biologicals for poultry/livestock = ag bioinputs. Analogous to Aquit and Feedvax (both Bioinputs)."),

    ("sciphage", "SciPhage", "startup_extended", "bio_theme_primary",
     "Bioinputs & Crop Resilience", SOURCE, "0.92",
     "Phage bioproducts for Salmonella in poultry/aquaculture. macro_theme=ag biologicals already confirms this."),

    ("geoprot", "Geoprot", "startup_extended", "bio_theme_primary",
     "Biomanufacturing & Fermentation Economy", SOURCE, "0.83",
     "Computational protein function prediction tool, not a drug. cluster=2 Biomanufacturing already correct. Therapeutics was error."),

    ("future_biome", "Future Biome", "startup_extended", "bio_theme_primary",
     "Food Systems & Alt Proteins", SOURCE, "0.88",
     "Fungi-based prebiotics = food/functional ingredients. macro_theme=food biotech confirms. Biomanufacturing was the HOW, not the WHAT."),

    # ── cluster_id corrections ─────────────────────────────────────────────
    ("antarka", "Antarka", "startup_extended", "cluster_id",
     "5", SOURCE, "0.90",
     "Cosmetic bio-ingredients from extremophile enzymes. cl=5 Biomaterials-Materials correct. cl=13 Diagnostics/Therapeutics was HDBSCAN error."),

    ("hybridon", "Hybridon", "startup_extended", "cluster_id",
     "1", SOURCE, "0.88",
     "Antimicrobial nanotech for materials/surfaces. cl=1 Biomaterials-Antimicrobial is exact match. cl=13 was HDBSCAN error."),

    ("heartbest", "Heartbest", "startup_extended", "cluster_id",
     "4", SOURCE, "0.87",
     "Plant-based dairy using plant ingredients, NOT precision fermentation. cl=4 Novel Ingredients correct. cl=15 Precision Fermentation was wrong."),

    ("microin", "MicroIN", "startup_extended", "cluster_id",
     "12", SOURCE, "0.86",
     "Microencapsulation for ag bioinputs. cl=12 Bioinputs-Biologicals Crop correct. cl=4 Food Systems was keyword-matching error (conf=0.35)."),

    ("seedmatriz", "SeedMatriz", "startup_extended", "cluster_id",
     "12", SOURCE, "0.86",
     "Seed encapsulation for ag inputs. cl=12 Bioinputs-Biologicals Crop correct. cl=20 Nature/Ecosystem was error (conf=0.35)."),

    ("nanotica", "Nanotica", "startup_extended", "cluster_id",
     "10", SOURCE, "0.86",
     "In-field nanoencapsulation for crop inputs/agrochemicals. cl=10 Bioinputs-Crop Protection correct. cl=20 was error (conf=0.35)."),

    ("beeflow", "Beeflow", "startup_extended", "cluster_id",
     "12", SOURCE, "0.88",
     "Pollination biologicals. cl=12 Bioinputs-Biologicals Crop correct after theme correction to Bioinputs."),

    ("phagelab", "PhageLab", "startup_extended", "cluster_id",
     "12", SOURCE, "0.90",
     "Animal health phage solutions for poultry/livestock = ag biologicals. cl=12 correct. cl=13 was Diagnostics error."),

    ("sciphage", "SciPhage", "startup_extended", "cluster_id",
     "12", SOURCE, "0.90",
     "Phage bioproducts for animal ag = ag biologicals. cl=12 correct. cl=13 was error."),

    ("done_properly", "Done Properly", "startup_extended", "cluster_id",
     "15", SOURCE, "0.85",
     "Uses fermentation (mycelium, flavor science) for food bio-ingredients. cl=15 Food Systems-Precision Fermentation. cl=2 Biomanufacturing-Industrial was wrong."),

    ("future_biome", "Future Biome", "startup_extended", "cluster_id",
     "4", SOURCE, "0.86",
     "Fungi prebiotics = food/functional ingredients. cl=4 Food Systems-Novel Ingredients correct after theme correction. cl=2 was error."),

    # ── scope change ──────────────────────────────────────────────────────
    ("logshare", "LogShare", "startup_extended", "scope_decision",
     "exclude", SOURCE, "0.92",
     "Pure freight-matching logistics platform. Bio connection is sustainability angle only — insufficient for BIO universe scope."),

    # ── country code fix ──────────────────────────────────────────────────
    ("circa_therapeutics", "Circa Therapeutics", "entities", "country_code",
     "AR", SOURCE, "0.97",
     "country_code AE (UAE) is data entry error. Company is Argentine (Buenos Aires HQ, confirmed PitchBook/RocketReach)."),
]

FIELDS = ["entity_id", "entity_name", "table_name", "field_name", "new_value", "source_url", "confidence", "notes"]

with OUT.open("a", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    for row in NEW_ROWS:
        w.writerow(dict(zip(FIELDS, row)))

print(f"Appended {len(NEW_ROWS)} rows to staging/entity_enrichments.csv")
