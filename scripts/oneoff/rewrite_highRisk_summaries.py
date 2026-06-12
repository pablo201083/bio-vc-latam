"""One-off: rewrite startup_summary_en for 11 high-risk semantic startups."""
import sqlite3, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from audit import diff_and_log_update

REWRITES = {
    "outpost": {
        "startup_summary_en": (
            "Outpost is a TechBio platform company making the human microbiome computationally tractable. "
            "It integrates high-throughput wet-lab microbiology with machine learning and foundation-model-style "
            "predictive systems in a closed-loop engine built for microbiome strain discovery, fermentation "
            "optimization, and biotech product development. Core applications span microbiome R&D services, "
            "computational strain modeling, and predictive biology tools for pharmaceutical and consumer-health "
            "customers."
        ),
    },
    "inner_cosmos": {
        "startup_summary_en": (
            "Inner Cosmos is a neurotechnology company developing a minimally invasive embedded brain-computer-"
            "interface therapy for treatment-resistant major depression. Its Digital Pill device reads and stimulates "
            "specific brain networks through a subgaleal implant, delivering closed-loop neuromodulation calibrated "
            "to individual neural signatures. The company has received FDA early-feasibility study authorization and "
            "is advancing clinical validation of the implant for psychiatric indications."
        ),
    },
    "cellco": {
        "startup_summary_en": (
            "CellCo applies synthetic biology, generative AI, and synthetic training data to design next-generation "
            "therapeutic molecules in biological domains where experimental data is scarce. Its platform builds "
            "computational models of complex biological systems to guide the design of novel medicines, targeting "
            "therapeutic areas where traditional trial-and-error drug discovery is slow or fails due to data "
            "limitations. The company focuses on precision therapeutics and engineered-biology drug candidates."
        ),
    },
    "tintte": {
        "startup_summary_en": (
            "Tintte is an Argentine biotech company producing natural biopigments through microbial fermentation "
            "to replace synthetic petroleum-derived textile dyes. Its bioprocess platform cultivates selected "
            "microorganisms that synthesize stable, vibrant colorants, eliminating toxic chemical inputs, reducing "
            "water consumption, and cutting energy use in dyeing operations. Tintte targets fashion and apparel "
            "manufacturers seeking drop-in biological substitutes for conventional synthetic dyes across natural "
            "and synthetic fiber substrates."
        ),
    },
    "alkemio": {
        "startup_summary_en": (
            "Alkemio develops a modular and scalable platform for sustainable separation and refining of rare earth "
            "elements and critical minerals. Its clean-chemistry process reduces capital expenditure and operational "
            "footprint relative to conventional solvent-extraction rare earth refining, and is designed to be "
            "adaptable across different ore feedstocks. The platform enables smaller-scale critical-material "
            "processing closer to end markets, reducing supply-chain concentration in rare earth value chains."
        ),
    },
    "vexxel_biotech": {
        "startup_summary_en": (
            "Vexxel Biotech develops protein-based encapsulation systems for precision delivery of agricultural "
            "biologicals and bioinputs to crops. Its platform uses engineered protein matrices to protect active "
            "biological compounds, including microbial inoculants, biocontrol agents, and biostimulants, from "
            "environmental degradation and to control their release at the target site. The encapsulation technology "
            "is designed to improve efficacy, shelf-life, and field performance of bioinputs versus conventional "
            "liquid or wettable-powder formulations."
        ),
    },
    "werk-nvac": {
        "startup_summary_en": (
            "WerkénVac is an Argentine aquaculture biotech company developing self-amplifying RNA vaccines for "
            "infectious diseases in farmed fish, targeting pathogens that devastate salmon and tilapia production. "
            "Its platform adapts mRNA vaccine technology for aquatic animal health, enabling faster and lower-cost "
            "vaccine manufacturing without live pathogen cultivation. By replacing prophylactic antibiotic use with "
            "biological immunization, WerkénVac addresses antimicrobial-resistance pressure in aquaculture food "
            "systems."
        ),
        "bio_theme_primary": "Bioinputs & Crop Resilience",
    },
    "neocell": {
        "startup_summary_en": (
            "Neocell provides end-to-end contract development and manufacturing services for biosimilars and "
            "biologic drugs, including insulins, monoclonal antibodies, growth hormones, and cytokines. The company "
            "covers cell-line construction, upstream and downstream bioprocess development, and cGMP-compliant "
            "manufacturing of preclinical and clinical batches. Its integrated CDMO model supports pharmaceutical "
            "and biotech companies bringing biosimilar and biologic products to Argentine and Latin American markets."
        ),
    },
    "arqlite": {
        "startup_summary_en": (
            "Arqlite converts hard-to-recycle multi-layer plastics and plastic composites into low-carbon "
            "lightweight aggregates used as substitutes for sand, gravel, and conventional fill in construction "
            "and civil engineering. Its thermomechanical upcycling process accepts plastic streams rejected by "
            "conventional recyclers, diverting them from landfill and incineration. Arqlite materials are certified "
            "for insulating fills, road sub-bases, green roofs, and lightweight concrete applications, displacing "
            "virgin mineral inputs with post-consumer circular materials."
        ),
    },
    "wiagro": {
        "startup_summary_en": (
            "Wiagro monitors stored grain and silo bags using IoT sensors, satellite connectivity, environmental "
            "data integration, predictive models, and digital traceability tools. Its Smart Silobag system detects "
            "temperature, humidity, and gas concentrations in real time to prevent post-harvest spoilage and "
            "mycotoxin formation. The platform also enables grain-provenance documentation and supply-chain "
            "traceability, helping producers and cooperatives capture quality premiums and comply with buyer "
            "verification requirements."
        ),
    },
    "frizata": {
        "startup_summary_en": (
            "Frizata is an Argentine company producing a direct-to-consumer line of flexitarian frozen meals, "
            "vegetables, and appetizers sold across Argentina, Chile, and Brazil. Its portfolio centers on meatless "
            "and reduced-meat items made without artificial preservatives, designed to help consumers lower their "
            "dependence on animal protein through convenient plant-forward frozen foods. Frizata operates at the "
            "intersection of alternative proteins and consumer-packaged goods, with a direct distribution model "
            "targeting urban households in Southern Cone markets."
        ),
    },
}

def main():
    conn = sqlite3.connect(ROOT / "db" / "bio_latam.db")
    conn.execute("PRAGMA journal_mode=WAL")
    total = 0
    for sid, fields in REWRITES.items():
        n = diff_and_log_update(
            conn, "startup_extended", "startup_id", sid,
            fields,
            actor="editorial/rewrite-high-risk-summaries",
            reason="Rewrite: remove editorial meta-commentary, expand bio signals, fix cluster instability",
        )
        print(f"  {sid:22s}  {n} campo(s)")
        total += n
    conn.commit()
    conn.close()
    print(f"\nTotal: {total} campos actualizados en startup_extended")

if __name__ == "__main__":
    main()
