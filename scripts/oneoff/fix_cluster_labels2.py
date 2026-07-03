"""
scripts/oneoff/fix_cluster_labels2.py — Segunda ronda de limpieza de sub_cluster_label.

Operaciones:
  A. Nulos: labels iguales al theme, singletons, y cruces de tema sin sub-grupo real
  B. Renames: nombres imprecisos o incompletos -> nombres funcionales
  C. Merge: "Circular Economy & Packaging" -> "Packaging Materials"
"""
import sqlite3, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))
from audit import diff_and_log_update

DB = ROOT / "db" / "bio_latam.db"
ACTOR = "oneoff/fix_cluster_labels2"

# (old_label, new_label_or_None, theme_filter_or_None)
OPERATIONS = [
    # ── A. NULL: label = theme name ─────────────────────────────────────────────
    ("Biomanufacturing & Platform Technologies", None, "Biomanufacturing & Platform Technologies"),
    ("Biomaterials & Green Chemistry",           None, "Biomaterials & Green Chemistry"),
    ("Diagnostics & Devices",                    None, "Diagnostics & Devices"),
    ("Food Systems & Alt Proteins",              None, "Food Systems & Alt Proteins"),
    ("Nature & Ecosystem Tech",                  None, "Nature & Ecosystem Tech"),
    ("Precision Agriculture",                    None, "Precision Agriculture"),

    # ── A. NULL: singletons / cross-theme sin masa critica ──────────────────────
    ("Post-Harvest Biotech",         None, None),
    ("Aquaculture Biologicals",      None, None),
    ("Carbon Credit",                None, None),
    ("Nanotechnology Antimicrobial", None, None),
    ("Genomics & Precision Medicine",None, None),
    ("Fermentation & Bioprocessing", None, None),
    ("Bioactives & Natural Chemistry",None,None),
    ("Alternative Proteins",         None, "Food Systems & Alt Proteins"),  # singleton (keep label if >1 elsewhere)
    ("Agrifood Supply Chain",        None, "Food Systems & Alt Proteins"),  # 1 rogue in Food
    ("Animal Health & Bioinputs",    None, "Therapeutics"),
    ("Molecular & Clinical Diagnostics", None, "Therapeutics"),  # 1 diag in Therapeutics
    ("Drug Discovery",               None, None),                # 2 misfit in Diagnostics

    # ── B. Renames: nombres funcionales ─────────────────────────────────────────
    ("Gene Editing",           "Crop Genetics & Precision Biotech",   "Bioinputs & Crop Resilience"),
    ("Crop Soil",              "Soil Health & Seed Biotech",          "Bioinputs & Crop Resilience"),
    ("Biologicals Bioinputs",  "Ag Biologicals & CDMO",               "Bioinputs & Crop Resilience"),
    ("Agro Industrial",        "Industrial Biotech & Green Chemistry","Biomaterials & Green Chemistry"),
    ("Circular Economy & Packaging", "Packaging Materials",           "Biomaterials & Green Chemistry"),
    ("Liquid Biopsy",          "Medical Devices & Precision Diagnostics","Diagnostics & Devices"),
    ("Cultivated Meat",        "Alternative Proteins & Aquaculture",  "Food Systems & Alt Proteins"),
    ("Microbiological Proteins","Marine Biotech & Aquaculture Ingredients","Food Systems & Alt Proteins"),
    ("Cancer Neurodegenerative","Oncology & CNS Therapeutics",        "Therapeutics"),
    ("Small Molecule",         "Drug Discovery Platforms",            "Therapeutics"),
    ("Biosimilar Monoclonal",  "Biologics & Drug Delivery",           "Therapeutics"),
    ("Tissue Organs",          "Tissue Engineering & Bioprinting",    "Therapeutics"),
]


def main(dry_run: bool = False):
    conn = sqlite3.connect(DB)
    total = 0

    for old_label, new_label, theme_filter in OPERATIONS:
        q = "SELECT startup_id FROM startup_extended WHERE sub_cluster_label = ?"
        params: list = [old_label]
        if theme_filter:
            q += " AND bio_theme_primary = ?"
            params.append(theme_filter)

        rows = conn.execute(q, params).fetchall()
        if not rows:
            print(f"  (0) {old_label!r} [{theme_filter or 'any'}]")
            continue

        action = f"-> {new_label!r}" if new_label else "-> NULL"
        print(f"  {len(rows):3d}  {old_label!r}  {action}  [{theme_filter or 'any'}]")
        total += len(rows)

        if dry_run:
            continue

        for (sid,) in rows:
            diff_and_log_update(
                conn=conn,
                table="startup_extended",
                row_id_col="startup_id",
                row_id=sid,
                new_values={"sub_cluster_label": new_label},
                actor=ACTOR,
                reason=f"label cleanup: {old_label!r} -> {new_label!r}",
            )

    conn.commit()
    conn.close()

    if dry_run:
        print(f"\n[dry-run] {total} filas afectadas")
    else:
        print(f"\nOK: {total} filas actualizadas")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    main(dry_run=args.dry_run)
