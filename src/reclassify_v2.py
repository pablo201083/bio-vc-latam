"""
src/reclassify_v2.py — BIO Editorial Category classifier v2

Arquitectura limpia de 2 fuentes, sin tags estructurados heredados:

  FUENTE A (prioridad): cluster_id → cluster_label → bio_theme
    Para las 489 startups en el mapa semántico.
    El cluster viene del embedding completo (1536 dims) curado a mano.
    Es la señal más rica disponible.

  FUENTE B (fallback): keyword scorer sobre startup_summary_en SOLAMENTE
    Para outliers (cluster_id = -1) o cuando la fuente A no está disponible.
    Sin domain_tags, bio_lens_tags, industry_codes ni macro_theme como inputs.
    Esas son clasificaciones manuales anteriores — se conservan como metadata
    pero no participan en la asignación de bio_theme.

  LOCKED: startups con corrección manual en audit_log (actor='human:curador')
    para bio_theme_primary son intocables. El clasificador las salta.

Cambios vs v1 (src/reclassify_v1_backup.py):
  - Fuente A (cluster) es nueva y primaria
  - Fuente B (keyword) conserva las mismas reglas semánticas pero sin tags
  - bio_theme_source ('cluster' | 'keyword' | 'locked') nuevo campo en audit
  - Las 30+ correcciones manuales quedan protegidas

Uso:
    python pipeline.py reclassify-themes       # corre v2 (default)
    python pipeline.py reclassify-themes --dry-run
    python pipeline.py reclassify-themes --use-v1  # vuelve al clasificador anterior
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT    = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "db" / "bio_latam.db"

# ── Los 8 temas canónicos ─────────────────────────────────────────────────────
BIO_THEMES = [
    "Diagnostics & Health Access",
    "Therapeutics",
    "Bioinputs & Crop Resilience",
    "Food Systems & Alt Proteins",
    "Biomanufacturing & Platform Technologies",
    "Biomaterials & Circular Economy",
    "Nature & Ecosystem Tech",
    "Farm Intelligence",
]

# ── Keyword scorer (summary_en SOLO — sin tags) ───────────────────────────────
# Importamos las reglas del v1 para no duplicarlas. Solo pasamos summary_en.
# Los tags estructurados quedan fuera del row que se pasa al scorer.
from src.reclassify_v1_backup import (
    score_startup as _score_v1,
    classify     as _classify_v1,
)


def _theme_from_cluster_label(label: str | None) -> str | None:
    """Extrae el bio_theme del cluster_label matcheando contra los 8 temas canónicos."""
    if not label:
        return None
    for theme in BIO_THEMES:
        if label.startswith(theme):
            return theme
    return None


def _keyword_score(summary_en: str | None) -> tuple[str | None, float]:
    """Keyword scorer sobre summary_en SOLAMENTE. Sin tags estructurados."""
    row = {
        "startup_summary_en": summary_en or "",
        "startup_summary_v1": "",
        "short_description":  "",
        # Tags vacíos — excluidos explícitamente
        "domain_tags":    "",
        "bio_lens_tags":  "",
        "tech_codes":     "[]",
        "industry_codes": "[]",
        "macro_theme":    "",
        "scope_basis":    "",
    }
    scores = _score_v1(row)
    primary, secondary, confidence = _classify_v1(scores)
    return primary, confidence


# ── DB layer ──────────────────────────────────────────────────────────────────

def _load_startups(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT
            sx.startup_id,
            e.canonical_name,
            sx.cluster_id,
            sx.cluster_label,
            sx.bio_theme_primary,
            sx.startup_summary_en,
            sx.startup_summary_v1,
            sx.bio_theme_confidence
        FROM startup_extended sx
        JOIN entities e ON e.entity_id = sx.startup_id
        WHERE sx.scope_decision = 'include'
        ORDER BY e.canonical_name
    """).fetchall()
    conn.row_factory = None
    return [dict(r) for r in rows]


def _locked_ids(conn: sqlite3.Connection) -> set[str]:
    """IDs de startups con corrección manual de bio_theme_primary — intocables."""
    return {
        row[0] for row in conn.execute("""
            SELECT DISTINCT entity_id FROM audit_log
            WHERE field = 'bio_theme_primary' AND actor = 'human:curador'
        """)
    }


# ── Clasificador principal ────────────────────────────────────────────────────

def classify_startup(row: dict, locked: set[str]) -> tuple[str | None, float, str]:
    """
    Retorna (bio_theme, confidence, source).
    source: 'locked' | 'cluster' | 'keyword' | 'keyword_conflict'
    """
    sid      = row["startup_id"]
    cl_id    = row["cluster_id"] if row["cluster_id"] is not None else -1
    cl_label = row["cluster_label"]
    summary  = row["startup_summary_en"] or row["startup_summary_v1"] or ""

    # 1. Locked — no tocar
    if sid in locked:
        return row["bio_theme_primary"], row["bio_theme_confidence"] or 1.0, "locked"

    # 2. En el mapa → cluster como fuente primaria
    if cl_id >= 0:
        cluster_theme = _theme_from_cluster_label(cl_label)
        if cluster_theme:
            # Validar con keyword para calcular confianza
            kw_theme, kw_conf = _keyword_score(summary)
            if kw_theme == cluster_theme:
                return cluster_theme, 0.90, "cluster"
            else:
                # Leve conflicto — el cluster gana pero marcamos
                return cluster_theme, 0.70, "cluster_conflict"

    # 3. Outlier o label faltante → keyword sobre summary
    kw_theme, kw_conf = _keyword_score(summary)
    return kw_theme, kw_conf, "keyword"


# ── Runner ────────────────────────────────────────────────────────────────────

def run(dry_run: bool = False, db_path: Path = DB_PATH) -> dict:
    conn   = sqlite3.connect(db_path)
    rows   = _load_startups(conn)
    locked = _locked_ids(conn)

    stats = {"locked": 0, "cluster": 0, "cluster_conflict": 0,
             "keyword": 0, "unchanged": 0, "updated": 0, "no_theme": 0}

    conflicts = []
    updates   = []

    for row in rows:
        new_theme, new_conf, source = classify_startup(row, locked)
        old_theme = row["bio_theme_primary"]

        stats[source if source in stats else "keyword"] += 1

        if new_theme is None:
            stats["no_theme"] += 1
            continue

        if new_theme == old_theme:
            stats["unchanged"] += 1
            continue

        updates.append((row["startup_id"], row["canonical_name"],
                        old_theme, new_theme, new_conf, source))
        stats["updated"] += 1

        if source == "cluster_conflict":
            conflicts.append((row["canonical_name"], old_theme, new_theme))

    # ── Reporte ──────────────────────────────────────────────────────────────
    print(f"\n=== reclassify-themes v2 {'(DRY RUN)' if dry_run else ''} ===")
    print(f"  Total startups    : {len(rows)}")
    print(f"  Locked (manual)   : {stats['locked']}")
    print(f"  Cluster → theme   : {stats['cluster']}")
    print(f"  Cluster (conflict): {stats['cluster_conflict']}")
    print(f"  Keyword fallback  : {stats['keyword']}")
    print(f"  Sin cambio        : {stats['unchanged']}")
    print(f"  Cambios a aplicar : {stats['updated']}")
    print(f"  Sin tema posible  : {stats['no_theme']}")

    if conflicts:
        print(f"\n  Conflictos cluster vs keyword ({len(conflicts)}) — cluster gana:")
        for name, old, new in conflicts[:20]:
            print(f"    {name[:38]:<38} kw={old[:28]:<28} cluster={new}")

    if dry_run:
        print("\n  (dry-run — no se escribe nada)")
        conn.close()
        return stats

    # ── Aplicar ──────────────────────────────────────────────────────────────
    import datetime
    now = datetime.datetime.now(datetime.UTC).isoformat()
    cur = conn.cursor()
    for sid, name, old_t, new_t, new_conf, source in updates:
        cur.execute(
            "UPDATE startup_extended SET bio_theme_primary=?, bio_theme_confidence=? WHERE startup_id=?",
            (new_t, round(new_conf, 3), sid),
        )
        cur.execute(
            """INSERT INTO audit_log
               (timestamp, actor, entity_id, table_name, field, old_value, new_value, reason)
               VALUES (?,?,?,?,?,?,?,?)""",
            (now, "auto:reclassify_v2", sid, "startup_extended",
             "bio_theme_primary", old_t, new_t,
             f"v2 source={source} conf={new_conf:.2f}"),
        )
    conn.commit()
    conn.close()
    print(f"\n  Commit OK — {stats['updated']} bio_theme_primary actualizados")
    return stats


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    run(dry_run=args.dry_run)
