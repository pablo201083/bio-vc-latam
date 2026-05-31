"""
scripts/compute_paradigm_positions.py

Computa las posiciones del Espacio de Paradigmas para cada startup,
basándose en sus tags semánticos (scale_tags, technology_tags, bio_lens_tags)
en lugar de centroides editoriales por tema.

Ejes:
  X: Nivel de organización biológica de la intervención
     (-1 = Molecular · · · +1 = Territorial/Planetaria)
  Y: Modo de creación de valor
     (-1 = Bio/Material · · · +1 = Digital/Computacional)

Las posiciones (en rango [-1,+1]) se escalan por CANVAS_SCALE y se guardan
en startup_extended.scatter_x / scatter_y. Luego regenera el JS del dashboard.

Workflow:
  1. python pipeline.py rebuild --phase clustering   (si hace falta reclustarizar)
  2. python scripts/compute_paradigm_positions.py
  El paso 2 sobreescribe scatter_x/scatter_y con las posiciones basadas en tags.
  Si se vuelve a correr clustering, repetir paso 2.

Uso:
  python scripts/compute_paradigm_positions.py
  python scripts/compute_paradigm_positions.py --dry-run   # solo imprime, no escribe
  python scripts/compute_paradigm_positions.py --no-jitter  # sin offset UMAP
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sqlite3
import sys
from typing import Optional

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DB_PATH   = ROOT / "db" / "bio_latam.db"
CANVAS_SCALE = 12.0   # [-1,+1] → [-12,+12]; SVG tiene rango ±17
JITTER_MAX   = 1.4    # unidades de canvas (post-escala) para separar puntos con score idéntico

# ── Tablas de scoring ────────────────────────────────────────────────────────

# Eje X — nivel de organización biológica de la intervención
# Se excluyen deliberadamente 'industrial-scale' y 'product-scale':
# son modos de producción, no niveles biológicos.
SCALE_X: dict[str, float] = {
    "molecular-scale":     -1.00,   # Moléculas, genes, proteínas
    "human-scale":          0.00,   # Cuerpo humano / organismo individual
    "agroecosystem-scale": +0.55,   # Campo, finca, cuenca
    "territorial-scale":   +0.85,   # Paisaje, uso del suelo regional
    "planetary-scale":     +1.00,   # Ciclos globales, terraformación
}

# technology_tags como señal secundaria de X
# (refuerza o reemplaza scale_tags cuando son ambiguos o ausentes)
TECH_X: dict[str, float] = {
    "therapeutics":      -0.80,
    "diagnostics":       -0.65,
    "synthetic-biology": -0.70,
    "fermentation":      -0.50,
    "biomaterials":      -0.20,
    "biomanufacturing":  -0.35,
    "bioinputs":         +0.25,
    "iot":               +0.40,
    "remediation":       +0.70,
    "remote-sensing":    +0.70,
    "carbon-mrv":        +0.80,
    # ai-data: cross-cutting, sin señal de escala propia
}

# Eje Y — modo de creación de valor (bio/material ↔ digital/computacional)
# technology_tags (peso 0.65)
TECH_Y: dict[str, float] = {
    "therapeutics":      -0.85,
    "fermentation":      -0.70,
    "synthetic-biology": -0.55,
    "bioinputs":         -0.50,
    "biomaterials":      -0.35,
    "biomanufacturing":  -0.20,
    "diagnostics":       +0.20,
    "remediation":       +0.30,
    "carbon-mrv":        +0.55,
    "iot":               +0.60,
    "remote-sensing":    +0.65,
    "ai-data":           +0.80,
}

# bio_lens_tags (peso 0.35)
LENS_Y: dict[str, float] = {
    "biobased":                          -0.50,
    "biocentric":                        -0.35,
    "human-health-bio":                  -0.20,
    "regenerative":                      -0.05,
    "circular":                          +0.10,
    "bio-enabled-industrial-transition": +0.25,
    "planetary-boundary":                +0.30,
}

# ── Parseo de tags ────────────────────────────────────────────────────────────

def parse_tags(field: Optional[str]) -> list[str]:
    if not field:
        return []
    return [t.strip() for t in field.split(";") if t.strip()]


def avg(tags: list[str], score_map: dict[str, float]) -> Optional[float]:
    vals = [score_map[t] for t in tags if t in score_map]
    return sum(vals) / len(vals) if vals else None


# ── Scoring por startup ───────────────────────────────────────────────────────

def score_x(row: dict) -> float:
    """Nivel de organización biológica: [-1, +1]."""
    scale_tags = [t for t in parse_tags(row.get("scale_tags")) if t in SCALE_X]
    tech_tags  = parse_tags(row.get("technology_tags"))

    s_scale = avg(scale_tags, SCALE_X)
    s_tech  = avg(tech_tags,  TECH_X)

    if s_scale is not None and s_tech is not None:
        return 0.75 * s_scale + 0.25 * s_tech
    return s_scale if s_scale is not None else (s_tech if s_tech is not None else 0.0)


def score_y(row: dict) -> float:
    """Paradigma bio/digital: [-1, +1]."""
    tech_tags = parse_tags(row.get("technology_tags"))
    lens_tags = parse_tags(row.get("bio_lens_tags"))

    s_tech = avg(tech_tags, TECH_Y)
    s_lens = avg(lens_tags, LENS_Y)

    if s_tech is not None and s_lens is not None:
        return 0.65 * s_tech + 0.35 * s_lens
    return s_tech if s_tech is not None else (s_lens if s_lens is not None else 0.0)


# ── Jitter via UMAP ───────────────────────────────────────────────────────────

def apply_umap_jitter(
    rows: list[dict],
    xs: list[float],
    ys: list[float],
) -> tuple[list[float], list[float]]:
    """Separa visualmente startups con score idéntico usando su offset UMAP normalizado.

    El offset es pequeño (≤ JITTER_MAX unidades de canvas) y no cambia la
    interpretación analítica — solo evita el solapamiento visual exacto.
    """
    from collections import defaultdict

    bins: dict[tuple, list[int]] = defaultdict(list)
    for i in range(len(rows)):
        key = (round(xs[i], 1), round(ys[i], 1))
        bins[key].append(i)

    rx, ry = xs[:], ys[:]

    for indices in bins.values():
        if len(indices) <= 1:
            continue
        umap = np.array([[rows[i].get("umap_x") or 0.0,
                          rows[i].get("umap_y") or 0.0] for i in indices])
        centroid = umap.mean(axis=0)
        offsets  = umap - centroid
        max_r    = np.linalg.norm(offsets, axis=1).max()
        if max_r > 0:
            offsets = offsets / max_r * JITTER_MAX
        for li, gi in enumerate(indices):
            rx[gi] = xs[gi] + offsets[li, 0]
            ry[gi] = ys[gi] + offsets[li, 1]

    return rx, ry


# ── Main ──────────────────────────────────────────────────────────────────────

def main(dry_run: bool = False, no_jitter: bool = False) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Asegurar columnas
    for col in ("scatter_x", "scatter_y"):
        try:
            conn.execute(f"ALTER TABLE startup_extended ADD COLUMN {col} REAL")
        except Exception:
            pass

    rows = conn.execute("""
        SELECT sx.startup_id, sx.scale_tags, sx.technology_tags, sx.bio_lens_tags,
               sx.bio_theme_primary AS bio_theme, sx.umap_x, sx.umap_y
        FROM startup_extended sx
        WHERE sx.scope_decision = 'include'
        ORDER BY sx.startup_id
    """).fetchall()
    rows = [dict(r) for r in rows]
    print(f"\nStartups include: {len(rows)}")

    raw_x = [score_x(r) for r in rows]
    raw_y = [score_y(r) for r in rows]

    # Escalar a canvas units primero, luego aplicar jitter en esas unidades
    sx = [v * CANVAS_SCALE for v in raw_x]
    sy = [v * CANVAS_SCALE for v in raw_y]

    if not no_jitter:
        sx, sy = apply_umap_jitter(rows, sx, sy)

    sx = [round(v, 3) for v in sx]
    sy = [round(v, 3) for v in sy]

    # ── Diagnóstico ───────────────────────────────────────────────────────────
    arr_x, arr_y = np.array(sx), np.array(sy)
    print(f"\n  Eje X (escala biológica): min={arr_x.min():.2f}  max={arr_x.max():.2f}  "
          f"mean={arr_x.mean():.2f}  σ={arr_x.std():.2f}")
    print(f"  Eje Y (paradigma):        min={arr_y.min():.2f}  max={arr_y.max():.2f}  "
          f"mean={arr_y.mean():.2f}  σ={arr_y.std():.2f}")

    # Distribución por cuadrante
    q_names = [
        ("Molecular + Bio (BioFarma)",        arr_x < 0,  arr_y < 0),
        ("Molecular + Digital (DiagTech)",     arr_x < 0,  arr_y >= 0),
        ("Sistémica + Bio (AgBio/Ecosistemas)",arr_x >= 0, arr_y < 0),
        ("Sistémica + Digital (AgData/NatTech)",arr_x >= 0,arr_y >= 0),
    ]
    print("\n  Cuadrantes:")
    for name, mx, my in q_names:
        n = int((mx & my).sum())
        print(f"    {n:3d}  {name}")

    # Muestra por tema
    from collections import defaultdict
    by_theme: dict[str, list] = defaultdict(list)
    for i, r in enumerate(rows):
        by_theme[r.get("bio_theme") or "?"].append((r["startup_id"], sx[i], sy[i]))

    print("\n  Promedios por tema (X=escala, Y=paradigma):")
    for theme in sorted(by_theme):
        vals = by_theme[theme]
        mx = sum(v[1] for v in vals) / len(vals)
        my = sum(v[2] for v in vals) / len(vals)
        print(f"    {theme[:40]:40s}  X={mx:+6.2f}  Y={my:+6.2f}  n={len(vals)}")

    if dry_run:
        print("\n[dry-run] Nada escrito. Revisar valores y correr sin --dry-run.")
        conn.close()
        return

    # ── Escritura ─────────────────────────────────────────────────────────────
    for i, row in enumerate(rows):
        conn.execute(
            "UPDATE startup_extended SET scatter_x=?, scatter_y=? WHERE startup_id=?",
            (sx[i], sy[i], row["startup_id"]),
        )
    conn.commit()
    print(f"\n  Escritos {len(rows)} registros → scatter_x / scatter_y")

    # ── Regenerar JS del dashboard ───────────────────────────────────────────
    from src.clustering import write_dashboard_data
    write_dashboard_data(conn)
    print("  Dashboard JS regenerado.")

    conn.close()
    print("\n[OK] Posiciones de paradigma computadas.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run",   action="store_true",
                        help="Calcular y mostrar, sin escribir en la DB")
    parser.add_argument("--no-jitter", action="store_true",
                        help="No aplicar offset UMAP; posiciones exactamente desde tags")
    args = parser.parse_args()
    main(dry_run=args.dry_run, no_jitter=args.no_jitter)
