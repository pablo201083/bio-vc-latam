"""
src/reconcile_themes.py — Frente B: clasificación que no se contradiga.

`validate` reportaba 92 conflictos bio_theme ≠ prefijo(cluster_label). El análisis
muestra que NO son 92 errores de clasificación: bio_theme_primary es la verdad
operativa (source-backed, editorial) y los clusters HDBSCAN son visuales; dos
clusters gruesos (0 "Precision Agriculture", 6 "Therapeutics") contienen subgrupos
temáticos coherentes que el clasificador editorial separa bien.

Este módulo tipifica cada conflicto en tres clases honestas:

- subcluster_coherent : el bio_theme forma un subgrupo de ≥SUB_MIN miembros dentro
                        del cluster. No es error: es un sub-cluster real (p.ej. los
                        33 Nature dentro del cluster agro, los 14 Diagnostics y 10
                        Biomateriales-nano dentro del cluster salud). Se les asigna
                        sub_cluster_label = bio_theme para alinear la capa visual.
- cross_cutting       : el bio_theme es transversal (Biomanufacturing & Platform
                        Technologies) y por diseño aparece disperso, no forma cluster
                        propio. Tampoco es error.
- isolated_review     : punto suelto cuyo bio_theme no coincide con ningún subgrupo
                        de su cluster. Estos sí son los conflictos genuinos que
                        requieren ojo humano (posible error de tema o caso único).

Salidas:
  quality/theme_cluster_mismatch_triage.csv — los 92 tipificados con evidencia.
Efecto en DB:
  sub_cluster_label poblado para subcluster_coherent + cross_cutting (auditado).

Uso:
    python pipeline.py reconcile-themes
    python pipeline.py reconcile-themes --dry-run
"""
from __future__ import annotations

import pathlib
import sqlite3
from collections import Counter, defaultdict

from src.audit import diff_and_log_update
from src.utils import write_csv

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Un bio_theme se reconoce como sub-cluster coherente si tiene al menos este
# número de miembros dentro del mismo cluster HDBSCAN.
SUB_MIN = 5

# Temas transversales: plataformas tecnológicas que sirven a múltiples verticales
# y por lo tanto no forman un cluster geométrico propio. Su dispersión es esperada.
CROSS_CUTTING_THEMES = {"Biomanufacturing & Platform Technologies"}


_CONF_MAP = {"low": 0.25, "medium": 0.55, "high": 0.85}


def _to_float(val) -> float:
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().lower()
    if s in _CONF_MAP:
        return _CONF_MAP[s]
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def _cl_prefix(cluster_label: str | None) -> str:
    if not cluster_label:
        return ""
    return cluster_label.split(" — ")[0].split("||")[0].strip()


def analyze(conn: sqlite3.Connection) -> list[dict]:
    """Devuelve los conflictos tipificados con su evidencia y acción sugerida."""
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute(
        """
        SELECT sx.startup_id, e.canonical_name, sx.bio_theme_primary,
               sx.cluster_label, sx.cluster_id, sx.cluster_confidence,
               sx.bio_theme_confidence, sx.scope_basis, sx.assignment_method,
               sx.sub_cluster_label
        FROM startup_extended sx JOIN entities e ON e.entity_id = sx.startup_id
        WHERE sx.scope_decision = 'include' AND sx.umap_x IS NOT NULL
        """
    ).fetchall()]
    conn.row_factory = None

    by_cluster: dict[int, list[dict]] = defaultdict(list)
    for r in rows:
        by_cluster[r["cluster_id"]].append(r)
    theme_count: dict[tuple[int, str], int] = {}
    cl_size: dict[int, int] = {}
    for cid, members in by_cluster.items():
        cl_size[cid] = len(members)
        for theme, n in Counter(m["bio_theme_primary"] for m in members).items():
            theme_count[(cid, theme)] = n

    triage: list[dict] = []
    for r in rows:
        bt, cl = r["bio_theme_primary"], r["cluster_label"]
        if not (bt and cl) or cl.startswith(bt):
            continue  # no es conflicto
        cid = r["cluster_id"]
        n_same = theme_count.get((cid, bt), 0)
        share = round(n_same / cl_size[cid], 3) if cl_size[cid] else 0.0

        if bt in CROSS_CUTTING_THEMES:
            verdict = "cross_cutting"
            action = "Tema transversal (plataforma): dispersión esperada. sub_cluster_label = bio_theme."
        elif n_same >= SUB_MIN:
            verdict = "subcluster_coherent"
            action = f"Subgrupo coherente ({n_same} del mismo tema en cluster {cid}). sub_cluster_label = bio_theme."
        else:
            verdict = "isolated_review"
            action = "Punto suelto: revisar si bio_theme es correcto o si es caso único. Sin cambio automático."

        triage.append({
            "startup_id": r["startup_id"],
            "name": r["canonical_name"],
            "bio_theme": bt,
            "cluster_label_prefix": _cl_prefix(cl),
            "cluster_id": cid,
            "n_same_theme_in_cluster": n_same,
            "theme_share_in_cluster": share,
            "bio_theme_confidence": round(_to_float(r["bio_theme_confidence"]), 3),
            "cluster_confidence": round(_to_float(r["cluster_confidence"]), 3),
            "scope_basis": r["scope_basis"] or "",
            "verdict": verdict,
            "suggested_action": action,
        })
    triage.sort(key=lambda t: (t["verdict"], t["bio_theme"], t["name"]))
    return triage


def run(db_path: pathlib.Path, dry_run: bool = False) -> dict:
    conn = sqlite3.connect(db_path)
    triage = analyze(conn)

    write_csv(ROOT / "quality" / "theme_cluster_mismatch_triage.csv", triage,
              ["startup_id", "name", "bio_theme", "cluster_label_prefix", "cluster_id",
               "n_same_theme_in_cluster", "theme_share_in_cluster", "bio_theme_confidence",
               "cluster_confidence", "scope_basis", "verdict", "suggested_action"])

    counts = Counter(t["verdict"] for t in triage)

    updated = 0
    if not dry_run:
        for t in triage:
            if t["verdict"] in ("subcluster_coherent", "cross_cutting"):
                updated += diff_and_log_update(
                    conn, "startup_extended", "startup_id", t["startup_id"],
                    {"sub_cluster_label": t["bio_theme"]},
                    actor="pipeline:reconcile_themes",
                    reason=(
                        f"Frente B reconcile: {t['verdict']} — sub_cluster_label "
                        f"alineado a bio_theme operativo dentro de cluster {t['cluster_id']}"
                    ),
                )
        conn.commit()

    conn.close()
    return {
        "total_conflicts": len(triage),
        "by_verdict": dict(counts),
        "sub_labels_updated": updated,
        "isolated_review": counts.get("isolated_review", 0),
        "dry_run": dry_run,
    }
