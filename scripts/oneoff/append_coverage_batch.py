"""Append CL-06 and CO-02 coverage sweep batch to staging/discovered_startups.csv."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAGING = ROOT / "staging" / "discovered_startups.csv"

NEW_ROWS = [
    # ── CL-06: 10 verifiable Chilean bio companies ──────────────────────────
    {
        "name": "Nalca Biotech",
        "country_code": "CL",
        "sector": "biomanufacturing",
        "description": (
            "Develops modular continuous fermentation systems to simplify and scale precision "
            "fermentation from lab to commercial production. Founded 2023 in Puerto Varas. "
            "Investors: Big Idea Ventures, Fundacion Ciencia & Vida. Raised $200K."
        ),
        "website": "nalca.bio",
        "founded_year": "2023",
        "source_url": "https://pitchbook.com/profiles/company/721009-45",
        "scope_recommendation": "include",
        "confidence": "0.92",
        "batch": "cl-06",
    },
    {
        "name": "Codebreaker Bioscience",
        "country_code": "CL",
        "sector": "agrobiotech",
        "description": (
            "Microbiome intelligence platform (Micro-ID) translating microbiome analysis into "
            "operational recommendations for aquaculture and agriculture. Winner of Startup del "
            "Chile 2026 (Banco de Chile). Based in Puerto Varas."
        ),
        "website": "codebreaker.bio",
        "founded_year": "",
        "source_url": (
            "https://www.salmonexpert.cl/biotecnologia-codebreaker-bioscience-inteligencia-microbiologica/"
            "codebreaker-bioscience-gana-startup-del-chile-y-proyecta-expansion-con-foco-en-salmonicultura/2074355"
        ),
        "scope_recommendation": "include",
        "confidence": "0.90",
        "batch": "cl-06",
    },
    {
        "name": "VioBact",
        "country_code": "CL",
        "sector": "aquabiotech",
        "description": (
            "UCN spinout developing marine probiotic consortia applied via rotifers to reduce "
            "antibiotic use and larval mortality in marine fish hatcheries. ANID Startup Ciencia "
            "2026 winner. Led by Dr. Rocio Urtubia."
        ),
        "website": "",
        "founded_year": "",
        "source_url": (
            "https://investigacion.ucn.cl/noticias/"
            "empresa-tecnologica-ucn-que-impacta-en-la-acuicultura-adjudico-fondo-startup-ciencia/"
        ),
        "scope_recommendation": "include",
        "confidence": "0.88",
        "batch": "cl-06",
    },
    {
        "name": "MycoSeaweed",
        "country_code": "CL",
        "sector": "food biotech",
        "description": (
            "Develops a novel microprotein superfood by bioconverting macroalgae with an artificial "
            "consortium of edible fungi. CORFO Crea y Valida funded. Founded by biotechnologist "
            "Catalina Landeta."
        ),
        "website": "",
        "founded_year": "",
        "source_url": (
            "https://www.cienciaenchile.cl/chile-pionero-en-biotecnologia-con-mycoseaweed"
            "-una-proteina-alternativa-del-futuro/"
        ),
        "scope_recommendation": "include",
        "confidence": "0.87",
        "batch": "cl-06",
    },
    {
        "name": "Infood Protein",
        "country_code": "CL",
        "sector": "insect biotech",
        "description": (
            "Produces insect flour, protein, oil and organic fertilizer from black soldier fly "
            "larvae via bioconversion of agricultural organic waste. Circular economy model. "
            "Founded 2018 in Valdivia. ANID research collaboration with UACh and INCAR."
        ),
        "website": "infoodprotein.com",
        "founded_year": "2018",
        "source_url": (
            "https://www.cienciaenchile.cl/infood-protein-biotechnology-spa-cientificos-presentan"
            "-una-fuente-alternativa-y-sustentable-de-proteinas-que-permitira-la-alimentacion"
            "-de-distintos-seres-vivos-para-el-sustento-del-ser-humano/"
        ),
        "scope_recommendation": "include",
        "confidence": "0.88",
        "batch": "cl-06",
    },
    {
        "name": "Inkus Biotech",
        "country_code": "CL",
        "sector": "agrobiotech",
        "description": (
            "Applies AI and advanced genomics to improve pathogen resistance and climate adaptation "
            "of aquatic species in salmon farming. CORFO COWO Los Lagos incubator. CEO Agustin Pina."
        ),
        "website": "",
        "founded_year": "",
        "source_url": (
            "https://www.salmonexpert.cl/alimentos-corfo-cowo/startups-de-base-tecnologica"
            "-desarrollan-innovadoras-soluciones-para-la-salmonicultura/1753757"
        ),
        "scope_recommendation": "include",
        "confidence": "0.82",
        "batch": "cl-06",
    },
    {
        "name": "Ayni Desert Interaction",
        "country_code": "CL",
        "sector": "bioinputs",
        "description": (
            "Develops agricultural bioinputs from native microorganisms of the Atacama Desert "
            "adapted to extreme UV radiation, salinity, and drought. UCN spinout, ANID Startup "
            "Ciencia 2026 winner, TRL 4. Led by Dr. Jonathan Fortt."
        ),
        "website": "",
        "founded_year": "",
        "source_url": (
            "https://investigacion.ucn.cl/noticias/"
            "microorganismos-del-desierto-de-atacama-como-solucion-biotecnologica-para-la-agricultura-extrema/"
        ),
        "scope_recommendation": "include",
        "confidence": "0.88",
        "batch": "cl-06",
    },
    {
        "name": "Pewman Innovation",
        "country_code": "CL",
        "sector": "bioinputs",
        "description": (
            "Develops bacterial biofortificants CRIOPROTECT (frost protection from Pseudomonas "
            "pewmanensis isolated in Antarctica) and NANOFORTE (Atacama+Antarctic microorganisms + "
            "oxygen nanobubbles). Founded 2019. $1M in public funding (CORFO+ANID+FIA). "
            "Mercurio 2024 Startup of the Year."
        ),
        "website": "pewmaninnovation.net",
        "founded_year": "2019",
        "source_url": (
            "https://www.cooperativaciencia.cl/radiociencia/2024/10/21/"
            "startup-chilena-usa-bacterias-para-desarrollar-soluciones-en-agricultura-y-otras-industrias/"
        ),
        "scope_recommendation": "include",
        "confidence": "0.91",
        "batch": "cl-06",
    },
    {
        "name": "Ecombio",
        "country_code": "CL",
        "sector": "aquabiotech",
        "description": (
            "Develops probiotic solutions for salmon to combat flavobacteriosis and reduce antibiotic "
            "use in freshwater aquaculture. Based in Concepcion. Founded 2013. Won Hemisferio Biotech "
            "2024 (CBT/SOFOFA Hub + ANID)."
        ),
        "website": "",
        "founded_year": "2013",
        "source_url": "https://ecosistemastartup.com/ecombio-reduce-uso-de-antibioticos-en-salmones/",
        "scope_recommendation": "include",
        "confidence": "0.87",
        "batch": "cl-06",
    },
    {
        "name": "Bee Technology",
        "country_code": "CL",
        "sector": "food biotech",
        "description": (
            "Develops FoodGuard, a biological food sanitizer using antimicrobial peptides that "
            "eliminates Salmonella, E.coli and Enterococci in fresh animal protein without synthetic "
            "additives, extending shelf life by 42%. Founded 2017. SAG-approved. Investors: "
            "The Ganesha Lab, Rio Baker. Eatable Adventures Raices program."
        ),
        "website": "beetechnology.cl",
        "founded_year": "2017",
        "source_url": "https://theganeshalab.com/startup/bee-technology/",
        "scope_recommendation": "include",
        "confidence": "0.90",
        "batch": "cl-06",
    },
    # ── CO-02: 1 verified Colombian bio company ──────────────────────────────
    {
        "name": "Koji",
        "country_code": "CO",
        "sector": "food biotech",
        "description": (
            "Combines Aspergillus oryzae (koji) fermentation, advanced bioprocessing, and data science "
            "to develop natural, functional, and traceable food ingredient solutions from Latin American "
            "biodiversity including Colombian coffee and regenerative crops. Eatable Adventures Raices "
            "2025 winner (EUR 100K + up to USD 1.1M follow-on potential). Backed by Alianza Team. "
            "Based in Bogota. Fi Europe 2024 Startup Challenge finalist."
        ),
        "website": "koji.com.co",
        "founded_year": "",
        "source_url": "https://latamlist.com/four-latin-american-startups-join-eatable-adventures-raices-acceleration-program/",
        "scope_recommendation": "include",
        "confidence": "0.90",
        "batch": "co-02",
    },
]


def main() -> None:
    with open(STAGING, encoding="utf-8-sig") as f:
        existing = list(csv.DictReader(f))

    existing_names = {r["name"].lower() for r in existing}
    dupes = [r["name"] for r in NEW_ROWS if r["name"].lower() in existing_names]
    if dupes:
        print(f"WARNING — already in file: {dupes}")
        return

    fields = list(existing[0].keys())
    with open(STAGING, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in existing:
            w.writerow(row)
        for row in NEW_ROWS:
            w.writerow(row)

    cl_new = sum(1 for r in NEW_ROWS if r["country_code"] == "CL")
    co_new = sum(1 for r in NEW_ROWS if r["country_code"] == "CO")
    print(f"Appended {len(NEW_ROWS)} rows ({cl_new} CL, {co_new} CO)")
    print(f"Total rows: {len(existing) + len(NEW_ROWS)}")


if __name__ == "__main__":
    main()
