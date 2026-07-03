"""
scripts/oneoff/fix_cluster_labels.py — Limpieza de 5 labels trampa en sub_cluster_label.

Problemas corregidos:
  1. "Biomanufacturing & Platform Technologies" = mismo nombre que el theme (22 filas) → NULL
  2. "Nature & Ecosystem Tech"               = mismo nombre que el theme (33 filas) → NULL
  3. "Point Care" en Diagnostics             → "Molecular & Clinical Diagnostics"
  4. "Shelf Life" en Food Systems            → "Functional Ingredients & Novel Foods"
  5. "Crop Monitoring" en Food Systems       → "Agrifood Supply Chain"
     "Crop Monitoring" en Precision Ag      → "Digital Crop & Livestock Intelligence"

Usa diff_and_log_update() para registrar cada cambio en audit_log.
"""
import sqlite3, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))
from audit import diff_and_log_update  # noqa: E402

DB = ROOT / "db" / "bio_latam.db"
SOURCE = "oneoff/fix_cluster_labels"

RENAMES = [
    # (old_label, new_label, bio_theme_filter)
    # 1 & 2 — same-as-theme → NULL
    ("Biomanufacturing & Platform Technologies", None, None),
    ("Nature & Ecosystem Tech",                  None, None),
    # 3 — Point Care catch-all
    ("Point Care",                "Molecular & Clinical Diagnostics", "Diagnostics & Devices"),
    ("Point Care",                "Molecular & Clinical Diagnostics", "Therapeutics"),
    # 4 — Shelf Life cross-theme
    ("Shelf Life", "Functional Ingredients & Novel Foods", "Food Systems & Alt Proteins"),
    ("Shelf Life", "Post-Harvest Biotech",                "Bioinputs & Crop Resilience"),
    # 5 — Crop Monitoring cross-theme
    ("Crop Monitoring", "Digital Crop & Livestock Intelligence", "Precision Agriculture"),
    ("Crop Monitoring", "Agrifood Supply Chain",                 "Food Systems & Alt Proteins"),
]


def main(dry_run: bool = False):
    conn = sqlite3.connect(DB)
    total = 0

    for old_label, new_label, theme_filter in RENAMES:
        query = "SELECT startup_id, sub_cluster_label FROM startup_extended WHERE sub_cluster_label = ?"
        params = [old_label]
        if theme_filter:
            query += " AND bio_theme_primary = ?"
            params.append(theme_filter)

        rows = conn.execute(query, params).fetchall()
        if not rows:
            print(f"  (0 filas) {old_label!r} [{theme_filter or 'any'}]")
            continue

        print(f"  {len(rows)} filas: {old_label!r} -> {new_label!r} [{theme_filter or 'any'}]")
        total += len(rows)

        if dry_run:
            continue

        for (sid,) in [(r[0],) for r in rows]:
            diff_and_log_update(
                conn=conn,
                table="startup_extended",
                row_id_col="startup_id",
                row_id=sid,
                new_values={"sub_cluster_label": new_label},
                actor=SOURCE,
                reason=f"label cleanup: {old_label!r} -> {new_label!r}",
            )

    conn.commit()
    conn.close()

    if dry_run:
        print(f"\n[dry-run] {total} filas afectadas — no se escribió nada")
    else:
        print(f"\nOK: {total} filas actualizadas")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    main(dry_run=args.dry_run)
