"""Assign bio_theme_primary to cl-06 and co-02 batch companies."""
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from audit import diff_and_log_update

DB = ROOT / "db" / "bio_latam.db"

THEME_ASSIGNMENTS = [
    # CL companies
    ("nalca-biotech-cl",           "Biomanufacturing & Platform Technologies",
     "Modular continuous fermentation systems — biomanufacturing infrastructure platform"),
    ("codebreaker-bioscience-cl",  "Farm Intelligence",
     "Microbiome intelligence platform for operational recommendations in aquaculture/agro"),
    ("viobact-cl",                 "Food Systems & Alt Proteins",
     "Marine probiotic consortia for fish larvae hatcheries — aquaculture animal health"),
    ("mycoseaweed-cl",             "Food Systems & Alt Proteins",
     "Seaweed+fungi bioconversion for alternative microprotein — novel food ingredient"),
    ("infood-protein-cl",          "Food Systems & Alt Proteins",
     "Black soldier fly protein and oil production from organic waste — insect biotech"),
    ("inkus-biotech-cl",           "Farm Intelligence",
     "AI+genomics platform for aquaculture pathogen resistance and climate adaptation"),
    ("ayni-desert-interaction-cl", "Bioinputs & Crop Resilience",
     "Atacama Desert extremophile microorganisms as agricultural bioinputs"),
    ("pewman-innovation-cl",       "Bioinputs & Crop Resilience",
     "Bacterial biofortificants (frost protection, drought resistance) from Antarctic/Atacama microorganisms"),
    ("ecombio-cl",                 "Food Systems & Alt Proteins",
     "Probiotics for salmon to combat flavobacteriosis and reduce antibiotic use"),
    ("Bee Technology",             "Food Systems & Alt Proteins",
     "Biological antimicrobial peptide sanitizer for fresh food safety (FoodGuard)"),
    # CO company
    ("koji-co",                    "Food Systems & Alt Proteins",
     "Koji fungal fermentation for natural food ingredients from Colombian biodiversity"),
]


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA journal_mode=WAL")
    total = 0

    for sid, theme, reason in THEME_ASSIGNMENTS:
        n = diff_and_log_update(
            conn, "startup_extended", "startup_id", sid,
            {
                "bio_theme_primary": theme,
                "is_bio_universe": 1,
                "bio_theme_confidence": 0.80,
            },
            actor="coverage/assign-themes-cl06-co02",
            reason=f"Manual theme assignment: {reason}",
        )
        status = "OK" if n else "skip"
        print(f"  {sid:45s} {theme[:35]:35s} {status}")
        total += n

    conn.commit()
    conn.close()
    print(f"\nTotal fields updated: {total}")


if __name__ == "__main__":
    main()
