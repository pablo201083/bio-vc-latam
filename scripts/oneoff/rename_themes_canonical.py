"""Canonical rename of 3 bio themes (2026-06-12).

  Farm Intelligence              -> Precision Agriculture
  Diagnostics & Health Access    -> Diagnostics & Devices
  Biomaterials & Circular Economy-> Biomaterials & Green Chemistry

Renombra (1) el valor en DB (bio_theme_primary + bio_theme_secondary, vía
diff_and_log_update con actor manual → mantiene el lock) y (2) los archivos
ACTIVOS de runtime. NO toca: scripts/oneoff/*, *_backup.py, pilot/*-data.js
(regenerados), reportes generados.
"""
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from audit import diff_and_log_update

DB = ROOT / "db" / "bio_latam.db"

RENAMES = [
    ("Farm Intelligence", "Precision Agriculture"),
    ("Diagnostics & Health Access", "Diagnostics & Devices"),
    ("Biomaterials & Circular Economy", "Biomaterials & Green Chemistry"),
]

# Archivos activos de runtime (drive behaviour). Excluye generados e históricos.
ACTIVE_FILES = [
    "src/clustering.py", "src/reclassify.py", "src/ecosystem_graph.py",
    "src/intelligence.py", "src/phylo_tree.py", "src/intro_builder.py",
    "src/bio_theme_overrides.py", "src/reconcile_themes.py", "src/merge_clusters.py",
    "src/taxonomy_cards.py",
    "pilot/startup-themes.html", "pilot/capital-atlas.html", "pilot/capital-atlas.js",
    "pilot/ecosystem-graph.html", "pilot/biolatam-map.html", "pilot/ecosystem-phylo.html",
    "pilot/cluster-quality.html", "pilot/quality-tracker.html", "pilot/theme-system.js",
    "quality/taxonomy_cards.md", "quality/bio_definition_operativa.md",
    "quality/sistema_clasificacion_visual.md", "quality/metodologia_clasificacion_clustering.md",
]


def rename_db(conn: sqlite3.Connection) -> int:
    total = 0
    for old, new in RENAMES:
        for field in ("bio_theme_primary", "bio_theme_secondary"):
            rows = conn.execute(
                f"SELECT startup_id FROM startup_extended WHERE {field} = ?", (old,)
            ).fetchall()
            for (sid,) in rows:
                total += diff_and_log_update(
                    conn, "startup_extended", "startup_id", sid,
                    {field: new},
                    actor="taxonomy/rename-canonical",
                    reason=f"Canonical rename: '{old}' -> '{new}'",
                )
    conn.commit()
    return total


def rename_files() -> dict:
    counts = {}
    for rel in ACTIVE_FILES:
        p = ROOT / rel
        if not p.exists():
            counts[rel] = "MISSING"
            continue
        text = p.read_text(encoding="utf-8")
        orig = text
        n = 0
        for old, new in RENAMES:
            n += text.count(old) + text.count(old.lower())
            text = text.replace(old, new).replace(old.lower(), new.lower())
        if text != orig:
            p.write_text(text, encoding="utf-8")
        counts[rel] = n
    return counts


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA journal_mode=WAL")
    db_n = rename_db(conn)
    conn.close()
    print(f"DB: {db_n} campos renombrados")
    print("Archivos:")
    for rel, n in rename_files().items():
        print(f"  {n!s:>6}  {rel}")


if __name__ == "__main__":
    main()
