"""
Deriva los campos de embedding que faltan en las 117 startups gridx_import_classified
sin llamar a ninguna API externa.

Campos derivados:
  macro_theme     → lookup desde bio_theme_primary
  emergent_theme  → cluster_label ya asignado por HDBSCAN (más específico)
  technology_tags → keyword matching sobre startup_summary_en + bio_theme_primary
  bio_lens_tags   → lookup desde bio_theme_primary
  business_one_liner → primera oración del summary (ya existe, pero lo forzamos si falta)

Salida: append a staging/entity_enrichments.csv
Ingestar con: python pipeline.py ingest-entity-enrichments
"""
import csv
import re
import sqlite3
import sys
from datetime import date
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT    = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "db" / "bio_latam.db"
STAGING = ROOT / "staging" / "entity_enrichments.csv"
SOURCE  = f"derive_missing_fields:{date.today()}"

# ── Mappings desde bio_theme_primary ─────────────────────────────────────────

MACRO_THEME = {
    "Therapeutics":                          "therapeutics and regenerative medicine",
    "Diagnostics & Health Access":           "diagnostics and medtech",
    "Bioinputs & Crop Resilience":           "ag biologicals and crop resilience",
    "Food Systems & Alt Proteins":           "food biotech and novel ingredients",
    "Nature & Ecosystem Tech":               "climate, energy and resource systems",
    "Farm Intelligence":                     "precision agriculture and resource intelligence",
    "Biomaterials & Circular Economy":       "biobased chemistry and advanced materials",
    "Biomanufacturing & Fermentation Economy": "biomanufacturing and bioindustrial platforms",
}

BIO_LENS = {
    "Therapeutics":                          "biobased; human-health-bio",
    "Diagnostics & Health Access":           "biobased; human-health-bio",
    "Bioinputs & Crop Resilience":           "biocentric",
    "Food Systems & Alt Proteins":           "biobased; bio-enabled-industrial-transition; human-health-bio",
    "Nature & Ecosystem Tech":               "biocentric; planetary-boundary",
    "Farm Intelligence":                     "biocentric; bio-enabled-industrial-transition",
    "Biomaterials & Circular Economy":       "biobased; bio-enabled-industrial-transition",
    "Biomanufacturing & Fermentation Economy": "biobased; bio-enabled-industrial-transition",
}

# Base tags por tema (siempre presentes)
BASE_TAGS = {
    "Therapeutics":                          ["therapeutics"],
    "Diagnostics & Health Access":           ["diagnostics"],
    "Bioinputs & Crop Resilience":           ["bioinputs"],
    "Food Systems & Alt Proteins":           [],
    "Nature & Ecosystem Tech":               [],
    "Farm Intelligence":                     ["remote-sensing", "ai-data"],
    "Biomaterials & Circular Economy":       ["biomaterials"],
    "Biomanufacturing & Fermentation Economy": ["biomanufacturing", "fermentation"],
}

# Reglas de keyword → tag adicional (sobre el summary)
KEYWORD_RULES = [
    (r"\b(artificial intelligence|machine learning|deep learning|\bAI\b|\bML\b|neural network|computer vision)\b", "ai-data"),
    (r"\b(IoT|internet of things|sensor|connected device|telemeter)\b", "iot"),
    (r"\b(satellite|remote sensing|NDVI|earth observation)\b", "remote-sensing"),
    (r"\b(ferment|fermentation|precision fermentation|brewing)\b", "fermentation"),
    (r"\b(synthetic biology|CRISPR|gene editing|gene therapy|genomic|genetic engineering)\b", "synthetic-biology"),
    (r"\b(carbon|CO2|greenhouse gas|emissions|sequestration|MRV)\b", "carbon-mrv"),
    (r"\b(enzyme|enzymatic|biocatalysis)\b", "enzymes"),
    (r"\b(bioremediation|remediation|decontamination|depollution)\b", "remediation"),
    (r"\b(precision fermentation|cell-free|cell free production)\b", "precision-fermentation"),
    (r"\b(biomanufacturing|bioproduction|bioprocess|fermentation platform)\b", "biomanufacturing"),
    (r"\b(biomaterial|biomimetic|biocomposite|biopolymer|bioink|bioprinting)\b", "biomaterials"),
]


def derive_tech_tags(summary: str, bio_theme: str) -> str:
    tags = list(BASE_TAGS.get(bio_theme, []))
    text = summary.lower()
    for pattern, tag in KEYWORD_RULES:
        if tag not in tags and re.search(pattern, text, re.IGNORECASE):
            tags.append(tag)
    # Siempre añadir ai-data si hay señal de AI y no está ya
    if "ai-data" not in tags and re.search(r"\bartificial intelligence\b|\bmachine learning\b|\bAI\b|\bneural\b|\bdeep learning\b", summary, re.IGNORECASE):
        tags.append("ai-data")
    return "; ".join(dict.fromkeys(tags))  # dedup preservando orden


def first_sentence(text: str) -> str:
    """Primera oración del summary como business_one_liner."""
    s = text.strip()
    m = re.search(r'[.!?]', s)
    if m:
        return s[:m.start()+1].strip()
    return s[:120].strip()


CSV_COLS = ["entity_id","entity_name","table_name","field_name","new_value","source_url","confidence","notes"]


def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT se.startup_id, e.canonical_name,
               se.bio_theme_primary, se.cluster_label,
               COALESCE(se.startup_summary_en, se.startup_summary_v1, '') as summary,
               se.macro_theme, se.emergent_theme, se.technology_tags,
               se.bio_lens_tags, se.business_one_liner
        FROM startup_extended se
        JOIN entities e ON e.entity_id = se.startup_id
        WHERE se.scope_decision = 'include'
          AND se.scope_reason = 'gridx_import'
    """)
    rows = c.fetchall()
    conn.close()

    print(f"Startups a enriquecer: {len(rows)}\n")

    exists = STAGING.exists()
    written = 0
    skipped = 0

    with STAGING.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLS)
        if not exists:
            w.writeheader()

        for sid, name, bio_theme, cluster_label, summary, \
            cur_macro, cur_emergent, cur_tech, cur_lens, cur_liner in rows:

            if not bio_theme:
                print(f"  SKIP {name} — sin bio_theme_primary")
                skipped += 1
                continue

            enrichments = []

            # macro_theme
            if not cur_macro:
                val = MACRO_THEME.get(bio_theme)
                if val:
                    enrichments.append(("macro_theme", val, "high"))

            # emergent_theme — usa cluster_label (lowercase, ya es descriptivo)
            if not cur_emergent and cluster_label:
                val = cluster_label.lower().replace("||", " · ").replace("|", " · ")
                enrichments.append(("emergent_theme", val, "medium"))

            # technology_tags
            if not cur_tech:
                val = derive_tech_tags(summary, bio_theme)
                if val:
                    enrichments.append(("technology_tags", val, "medium"))

            # bio_lens_tags
            if not cur_lens:
                val = BIO_LENS.get(bio_theme)
                if val:
                    enrichments.append(("bio_lens_tags", val, "medium"))

            # business_one_liner (si falta)
            if not cur_liner and summary:
                val = first_sentence(summary)
                if val:
                    enrichments.append(("business_one_liner", val, "medium"))

            for field, val, conf in enrichments:
                w.writerow({
                    "entity_id": sid, "entity_name": name,
                    "table_name": "startup_extended",
                    "field_name": field, "new_value": val,
                    "source_url": SOURCE, "confidence": conf,
                    "notes": f"derived from bio_theme_primary / cluster_label",
                })
                written += 1

            tag_str = derive_tech_tags(summary, bio_theme)
            print(f"  {name[:35]:35}  macro=✓  tags={tag_str[:40]}")

    print(f"\nEscrito: {written} filas | Skipped: {skipped}")
    print(f"\nSiguiente:")
    print(f"  python pipeline.py ingest-entity-enrichments")
    print(f"  python pipeline.py rebuild --phase embeddings")
    print(f"  python pipeline.py rebuild --phase clustering")


if __name__ == "__main__":
    main()
