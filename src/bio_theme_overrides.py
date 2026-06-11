"""
src/bio_theme_overrides.py — compuerta auditable de bio_theme_primary.

El clasificador `src/reclassify.py` (keyword scorer v3) está descalibrado respecto
del estado curado: correrlo reasignaría masivamente con errores groseros (p.ej.
Aegro → Nature). Por eso el bio_theme operativo NO se regenera con el scorer; se
mantiene con curaduría encima. Este módulo es la compuerta para corregir casos
puntuales con evidencia, igual que manual_semantic_theme_overrides.csv lo es para
la capa semántica.

Lee quality/manual_bio_theme_overrides.csv y aplica bio_theme_primary (y opcional
is_bio_universe) vía diff_and_log_update. Idempotente.

IMPORTANTE: si algún día se re-sincroniza y corre `reclassify-themes`, estos
overrides deben re-aplicarse después (son la última palabra editorial).

Uso:
    python pipeline.py apply-bio-overrides
    python pipeline.py apply-bio-overrides --dry-run
"""
from __future__ import annotations

import pathlib
import sqlite3

from src.audit import diff_and_log_update
from src.utils import clean, load_csv

ROOT = pathlib.Path(__file__).resolve().parent.parent
OVERRIDE_CSV = ROOT / "quality" / "manual_bio_theme_overrides.csv"

VALID_THEMES = {
    "Farm Intelligence", "Bioinputs & Crop Resilience", "Food Systems & Alt Proteins",
    "Biomaterials & Circular Economy", "Nature & Ecosystem Tech",
    "Diagnostics & Health Access", "Therapeutics",
    "Biomanufacturing & Platform Technologies",
}


def run(db_path: pathlib.Path, dry_run: bool = False) -> dict:
    rows = load_csv(OVERRIDE_CSV)
    conn = sqlite3.connect(db_path)

    applied = 0
    skipped: list[str] = []
    unknown_theme: list[str] = []
    missing: list[str] = []
    changes: list[tuple[str, str, str]] = []  # (id, from, to)

    for r in rows:
        sid = clean(r.get("startup_id"))
        theme = clean(r.get("bio_theme_primary"))
        if not sid or not theme:
            continue
        if theme not in VALID_THEMES:
            unknown_theme.append(f"{sid} → {theme}")
            continue

        cur = conn.execute(
            "SELECT bio_theme_primary, is_bio_universe FROM startup_extended WHERE startup_id=?", (sid,)
        ).fetchone()
        if cur is None:
            missing.append(sid)
            continue
        old_theme = cur[0] or "—"
        old_bio = cur[1]

        new_values = {"bio_theme_primary": theme}
        is_bio = clean(r.get("is_bio_universe"))
        bio_changes = False
        if is_bio in ("0", "1"):
            new_values["is_bio_universe"] = int(is_bio)
            bio_changes = (old_bio != int(is_bio))

        # Nada que aplicar si ni el tema ni is_bio_universe difieren del estado actual.
        if old_theme == theme and not bio_changes:
            skipped.append(sid)
            continue

        # Etiqueta del cambio (tema y/o intensidad biológica).
        label_from = old_theme + (f" bio={old_bio}" if bio_changes else "")
        label_to = theme + (f" bio={is_bio}" if bio_changes else "")
        changes.append((sid, label_from, label_to))
        if not dry_run:
            applied += diff_and_log_update(
                conn, "startup_extended", "startup_id", sid,
                new_values,
                actor="curator:bio_theme_override",
                reason=f"manual_bio_theme_overrides.csv — {clean(r.get('override_reason'))[:200]}",
                evidence_url=clean(r.get("evidence_url")) or None,
            )

    if not dry_run:
        conn.commit()
    conn.close()

    return {
        "rows": len(rows),
        "changes": changes,
        "applied_fields": applied,
        "already_correct": len(skipped),
        "unknown_theme": unknown_theme,
        "missing_startup": missing,
        "dry_run": dry_run,
    }
