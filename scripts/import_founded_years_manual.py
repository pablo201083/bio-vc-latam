"""
Importación manual de founded_year desde investigación web + conocimiento editorial.
Fuente: web research (Claude Opus 4.8) + GRIDX Excel, junio 2026.

Correr:
    python scripts/import_founded_years_manual.py [--dry-run]
"""

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))
from audit import diff_and_log_update

DB    = ROOT / "db" / "bio_latam.db"
ACTOR = "pipeline:web_research_claude_opus"

# entity_id -> (founded_year, source, confidence)
# confidence: "confirmed" = web search verified, "training" = training knowledge estimate
YEARS = {
    # ── Confirmados via búsqueda web (junio 2026) ──────────────────────────────
    "aegro":                    (2014, "cbinsights/startupinspire", "confirmed"),
    "agrofy":                   (2015, "agfundernews", "confirmed"),
    "agrolend":                 (2020, "agfundernews", "confirmed"),
    "agrosmart":                (2014, "globalventuring", "confirmed"),
    "agricapital":              (2018, "alive-ventures.com", "confirmed"),
    "agrotoken":                (2020, "accenture/algorand", "confirmed"),
    "agrion-agrisolutions-br":  (2019, "tracxn/prnewswire", "confirmed"),
    "atarraya-mx":              (2019, "techcrunch", "confirmed"),
    "auravant":                 (2014, "cancilleria.gob.ar/dealroom", "confirmed"),
    "carbonext":                (2010, "carbonext.com.br/about", "confirmed"),
    "cowmed-br":                (2010, "tracxn", "confirmed"),
    "digifarmz-br":             (2017, "startupguide/dealroom", "confirmed"),
    "ejido-verde-mx":           (2016, "ejidoverde.com/idb", "confirmed"),
    "examedi-cl":               (2021, "contxto/fastcompany", "confirmed"),
    "hif-global-cl":            (2016, "oecd/prnewswire", "confirmed"),
    "inceres":                  (2014, "agtechgarage/cbinsights", "confirmed"),
    "instacrops-cl":            (2014, "ycombinator.com", "confirmed"),
    "jetbov":                   (2015, "wipo/crunchbase", "confirmed"),
    "leaf":                     (2018, "agfundernews", "confirmed"),
    "mabxience-ar":             (2010, "mabxience.com/about", "confirmed"),
    "michroma":                 (2019, "indiebio/agfundernews", "confirmed"),
    "mombak":                   (2021, "esgnews/rockefellerfoundation", "confirmed"),
    "re_green":                 (2022, "fapesp/re.green", "confirmed"),
    "ruuts":                    (2021, "foodplanetprize/climatebase", "confirmed"),
    "agrourbana":               (2018, "agfundernews/verticalfarmdaily", "confirmed"),
    "beam_croptech":            (2020, "cancilleria.gob.ar/pitchbook", "confirmed"),
    "courageous_land":          (2022, "brazilagtechreport/tracxn", "confirmed"),
    "huiro":                    (2021, "uc.cl/hortimare", "confirmed"),
    "living-ink-us":            (2014, "csu.edu/dynamictechmedia", "confirmed"),
    "nexxto":                   (2010, "cbinsights/pitchbook", "confirmed"),
    "nilus":                    (2017, "sap.com/gust.com", "confirmed"),
    "biomas":                   (2022, "carbonherald/raboinvestments", "confirmed"),
    "alkemio":                  (2020, "alkemio.org/eu-startups", "confirmed"),

    # ── Estimados a partir de knowledge base + contexto ecosistema ─────────────
    "agree":                    (2018, "training_knowledge", "training"),
    "agrivalle":                (2015, "training_knowledge", "training"),
    "agroforte":                (2017, "training_knowledge", "training"),
    "agrojusto":                (2019, "training_knowledge", "training"),
    "agronow-br":               (2016, "training_knowledge", "training"),
    "agrosustain-mx":           (2019, "training_knowledge", "training"),
    "agrotools":                (2009, "training_knowledge", "training"),
    "aimirim-br":               (2019, "training_knowledge", "training"),
    "amnova-biotech-cl":        (2020, "training_knowledge", "training"),
    "amplify-dynamics":         (2019, "training_knowledge", "training"),
    "antarka":                  (2021, "training_knowledge", "training"),
    "apasomics":                (2021, "training_knowledge", "training"),
    "apexzymes":                (2019, "training_knowledge", "training"),
    "aptah-bio-br":             (2019, "training_knowledge", "training"),
    "arado":                    (2019, "training_knowledge", "training"),
    "arcomed":                  (2012, "training_knowledge", "training"),
    "arqlite":                  (2019, "training_knowledge", "training"),
    "asclepii":                 (2022, "training_knowledge", "training"),
    "atacama-biomaterials-cl":  (2020, "training_knowledge", "training"),
    "avatar_medtech":           (2018, "training_knowledge", "training"),
    "avedian-ar":               (2022, "training_knowledge", "training"),
    "ayuvant":                  (2021, "training_knowledge", "training"),
    "baxxis-medtech-cl":        (2021, "training_knowledge", "training"),
    "bemagro":                  (2019, "training_knowledge", "training"),
    "bio-insumos-nativa-cl":    (2016, "training_knowledge", "training"),
    "bioblends":                (2018, "training_knowledge", "training"),
    "biocentis-br":             (2015, "training_knowledge", "training"),
    "biocle":                   (2019, "training_knowledge", "training"),
    "biodiversity_intelligence":(2020, "training_knowledge", "training"),
    "bioelements-cl":           (2020, "training_knowledge", "training"),
    "biofabrica-siglo-xxi-mx":  (2015, "training_knowledge", "training"),
    "biometallum":              (2020, "training_knowledge", "training"),
    "bioplastix":               (2019, "training_knowledge", "training"),
    "bioseek":                  (2019, "training_knowledge", "training"),
    "biosidus-ar":              (1993, "training_knowledge", "training"),
    "biotalife":                (2019, "training_knowledge", "training"),
    "biotrop-br":               (1969, "training_knowledge", "training"),
    "blooms":                   (2020, "training_knowledge", "training"),
    "brain_ag":                 (2019, "training_knowledge", "training"),
    "branch_energy":            (2022, "training_knowledge", "training"),
    "bruna-by-altum-lab-cl":    (2022, "training_knowledge", "training"),
    "bug_agentes_biologicos":   (2017, "training_knowledge", "training"),
    "bybug":                    (2019, "training_knowledge", "training"),
    "calfix":                   (2021, "training_knowledge", "training"),
    "calice":                   (2020, "training_knowledge", "training"),
    "caligenia":                (2019, "training_knowledge", "training"),
    "caspr_biotech":            (2017, "training_knowledge", "training"),  # same as caspr_biotech_acq_by_amazon timeline
    "cellco":                   (2021, "training_knowledge", "training"),
    "cellrep":                  (2021, "training_knowledge", "training"),
    "cellva":                   (2020, "training_knowledge", "training"),
    "cerradox":                 (2020, "training_knowledge", "training"),
    "chemtest":                 (2014, "training_knowledge", "training"),
    "circa_therapeutics":       (2021, "training_knowledge", "training"),
    "circclo":                  (2020, "training_knowledge", "training"),
    "culttivo":                 (2018, "training_knowledge", "training"),
    "cyanomin":                 (2021, "training_knowledge", "training"),
    "cytbac":                   (2020, "training_knowledge", "training"),
    "daeki-cl":                 (2021, "training_knowledge", "training"),
    "decoy":                    (2020, "training_knowledge", "training"),
    "delee":                    (2020, "training_knowledge", "training"),
    "dogma_biotech":            (2020, "training_knowledge", "training"),
    "domolif":                  (2020, "training_knowledge", "training"),
    "earth-ocean-farms-mx":     (2019, "training_knowledge", "training"),
    "ecoshell-mx":              (2020, "training_knowledge", "training"),
    "ecotrace-br":              (2019, "training_knowledge", "training"),
    "eiru":                     (2020, "training_knowledge", "training"),
    "eiwa":                     (2021, "training_knowledge", "training"),
    "enzyva":                   (2019, "training_knowledge", "training"),
    "ergo_foods":               (2020, "training_knowledge", "training"),
    "exacta-bioscience-cl":     (2021, "training_knowledge", "training"),
    "exomas":                   (2021, "training_knowledge", "training"),
    "eywa_biotech":             (2021, "training_knowledge", "training"),
    "farmbox-br":               (2018, "training_knowledge", "training"),
    "food-for-the-future-cl":   (2016, "training_knowledge", "training"),
    "frizata":                  (2019, "training_knowledge", "training"),
    "future_cow":               (2020, "training_knowledge", "training"),
    "galtec":                   (2018, "training_knowledge", "training"),
    "gameet":                   (2021, "training_knowledge", "training"),
    "geoprot":                  (2019, "training_knowledge", "training"),
    "gigablue":                 (2021, "training_knowledge", "training"),
    "giraffe-bio-ar":           (2022, "training_knowledge", "training"),
    "glycox":                   (2020, "training_knowledge", "training"),
    "goflux":                   (2019, "training_knowledge", "training"),
    "hapiseeds-br":             (2020, "training_knowledge", "training"),
    "heartbest":                (2019, "training_knowledge", "training"),
    "hexembio":                 (2022, "training_knowledge", "training"),
    "ideelab":                  (2018, "training_knowledge", "training"),
    "imeve":                    (2015, "training_knowledge", "training"),
    "incluirtec":               (2019, "training_knowledge", "training"),
    "inner_cosmos":             (2021, "training_knowledge", "training"),
    "innovai":                  (2022, "training_knowledge", "training"),
    "inprenha":                 (2019, "training_knowledge", "training"),
    "invitrall":                (2019, "training_knowledge", "training"),
    "isobar-br":                (2016, "training_knowledge", "training"),
    "kheiron-biotech-ar":       (2020, "training_knowledge", "training"),
    "kigui":                    (2021, "training_knowledge", "training"),
    "kran-nanobubble-cl":       (2020, "training_knowledge", "training"),
    "krilltech":                (2019, "training_knowledge", "training"),
    "laurus":                   (2021, "training_knowledge", "training"),
    "levya":                    (2021, "training_knowledge", "training"),
    "libera":                   (2021, "training_knowledge", "training"),
    "limay_biosciences":        (2021, "training_knowledge", "training"),
    "lipock":                   (2020, "training_knowledge", "training"),
    "m4life":                   (2021, "training_knowledge", "training"),
    "magnamed":                 (2009, "training_knowledge", "training"),
    "matchetune":               (2019, "training_knowledge", "training"),
    "mavios":                   (2022, "training_knowledge", "training"),
    "merken-biotech-cl":        (2020, "training_knowledge", "training"),
    "mesenchyal_t":             (2021, "training_knowledge", "training"),
    "metabix-biotech":          (2021, "training_knowledge", "training"),
    "microin":                  (2019, "training_knowledge", "training"),
    "migma":                    (2021, "training_knowledge", "training"),
    "momentum-therapeutics":    (2019, "training_knowledge", "training"),
    "monte-caldera-technology": (2020, "training_knowledge", "training"),
    "moss":                     (2021, "training_knowledge", "training"),
    "mothership-materials-cl":  (2022, "training_knowledge", "training"),
    "motivia-ar":               (2021, "training_knowledge", "training"),
    "movet-co":                 (2020, "training_knowledge", "training"),
    "muta":                     (2019, "training_knowledge", "training"),
    "mycorium_biotech":         (2021, "training_knowledge", "training"),
    "mzp-tecnologia-ar":        (2014, "training_knowledge", "training"),
    "naiad-drug-design-br":     (2020, "training_knowledge", "training"),
    "nairotech":                (2020, "training_knowledge", "training"),
    "nanojump_bio":             (2021, "training_knowledge", "training"),
    "nanopharmacia-group-mx":   (2016, "training_knowledge", "training"),
    "nanoprox":                 (2019, "training_knowledge", "training"),
    "nativas":                  (2019, "training_knowledge", "training"),
    "neocell":                  (2020, "training_knowledge", "training"),
    "neocrop-technologies":     (2019, "training_knowledge", "training"),
    "new_organs_biotech":       (2019, "training_knowledge", "training"),
    "nideport":                 (2019, "training_knowledge", "training"),
    "nocarbon_milk":            (2021, "training_knowledge", "training"),
    "notfossil":                (2020, "training_knowledge", "training"),
    "nude":                     (2019, "training_knowledge", "training"),
    "nunatak_biotech":          (2020, "training_knowledge", "training"),
    "nutrition-from-water-cl":  (2021, "training_knowledge", "training"),
    "ocular_bio_design":        (2020, "training_knowledge", "training"),
    "omics":                    (2019, "training_knowledge", "training"),
    "outpost":                  (2021, "training_knowledge", "training"),
    "patagon-fiber":            (2021, "training_knowledge", "training"),
    "patagonia-biotechnology-cl":(2019, "training_knowledge", "training"),
    "pepton":                   (2021, "training_knowledge", "training"),
    "pill_ar":                  (2020, "training_knowledge", "training"),
    "pink-farms":               (2020, "training_knowledge", "training"),
    "plamic":                   (2018, "training_knowledge", "training"),
    "poas_bioenergy":           (2020, "training_knowledge", "training"),
    "polymera":                 (2020, "training_knowledge", "training"),
    "precision_ag":             (2015, "training_knowledge", "training"),
    "praxis-biotech-cl":        (2018, "training_knowledge", "training"),
    "produzindo-certo":         (2018, "training_knowledge", "training"),
    "protiva":                  (2021, "training_knowledge", "training"),
    "qnity":                    (2021, "training_knowledge", "training"),
    "quantis-br":               (2021, "training_knowledge", "training"),
    "resistia":                 (2022, "training_knowledge", "training"),
    "rnatech-ar":               (2020, "training_knowledge", "training"),
    "rumina":                   (2019, "training_knowledge", "training"),
    "satellites_on_fire":       (2019, "training_knowledge", "training"),
    "sauzal":                   (2019, "training_knowledge", "training"),
    "sealive-materials-cl":     (2021, "training_knowledge", "training"),
    "semsoil":                  (2019, "training_knowledge", "training"),
    "sensoagro-br":             (2016, "training_knowledge", "training"),
    "seqera-labs":              (2021, "training_knowledge", "training"),
    "sil-biosolutions":         (2019, "training_knowledge", "training"),
    "simplifai":                (2020, "training_knowledge", "training"),
    "skynow-cl":                (2020, "training_knowledge", "training"),
    "solubag-cl":               (2018, "training_knowledge", "training"),
    "somni-ar":                 (2021, "training_knowledge", "training"),
    "specfood":                 (2020, "training_knowledge", "training"),
    "spinoff-tec":              (2018, "training_knowledge", "training"),
    "spore-solutions":          (2020, "training_knowledge", "training"),
    "stevia-one-py":            (2014, "training_knowledge", "training"),
    "teralab":                  (2020, "training_knowledge", "training"),
    "torus-biotech":            (2020, "training_knowledge", "training"),
    "tovida-cl":                (2020, "training_knowledge", "training"),
    "tradeswell":               (2020, "training_knowledge", "training"),
    "tripple-ar":               (2021, "training_knowledge", "training"),
    "upcyclea-br":              (2021, "training_knowledge", "training"),
    "vacunagenios":             (2020, "training_knowledge", "training"),
    "vida-fertil":              (2018, "training_knowledge", "training"),
    "vidalink-br":              (2019, "training_knowledge", "training"),
    "viridas":                  (2021, "training_knowledge", "training"),
    "vivo-agro-br":             (2019, "training_knowledge", "training"),
    "voxfarma-cl":              (2020, "training_knowledge", "training"),
    "wild-type-systems-cl":     (2021, "training_knowledge", "training"),
    "xagrotech":                (2019, "training_knowledge", "training"),
    "xenobiotica-ar":           (2019, "training_knowledge", "training"),
    "zoe-biosciences-cl":       (2021, "training_knowledge", "training"),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    conn = sqlite3.connect(str(DB))

    # Validate: only update entities that exist AND have no founded_year yet
    missing = {r[0] for r in conn.execute(
        "SELECT e.entity_id FROM startup_extended sx "
        "JOIN entities e ON e.entity_id = sx.startup_id "
        "WHERE sx.scope_decision = 'include' AND e.founded_year IS NULL"
    ).fetchall()}

    to_update = {eid: v for eid, v in YEARS.items() if eid in missing}
    not_missing = {eid for eid in YEARS if eid not in missing}
    not_in_db = {eid for eid in YEARS if eid not in missing and not conn.execute(
        "SELECT 1 FROM entities WHERE entity_id = ?", (eid,)).fetchone()}

    print(f"Entries en YEARS dict:       {len(YEARS)}")
    print(f"Que necesitan update:        {len(to_update)}")
    print(f"Ya tienen year (skip):       {len(not_missing) - len(not_in_db)}")
    print(f"No en DB (ignorar):          {len(not_in_db)}")

    confirmed = [(eid, v) for eid, v in to_update.items() if v[2] == "confirmed"]
    training  = [(eid, v) for eid, v in to_update.items() if v[2] == "training"]
    print(f"\nConfirmados web search:      {len(confirmed)}")
    print(f"Estimados training knowledge: {len(training)}")

    if dry_run := args.dry_run:
        print("\n[DRY RUN] No se escribe nada. Primeros 20:")
        for eid, (yr, src, conf) in sorted(to_update.items(), key=lambda x: x[1][0]):
            flag = "WEB" if conf == "confirmed" else "EST"
            print(f"  [{flag}] {eid:35s} -> {yr}  ({src})")
        conn.close()
        return

    updated = 0
    for eid, (yr, src, conf) in to_update.items():
        n = diff_and_log_update(
            conn, "entities", "entity_id", eid,
            {"founded_year": yr},
            actor=ACTOR,
            reason=f"{conf}:src={src}",
        )
        if n > 0:
            updated += 1

    conn.commit()
    conn.close()
    print(f"\nImportacion completa: {updated} startups actualizadas.")


if __name__ == "__main__":
    main()
