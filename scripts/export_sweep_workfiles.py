"""
scripts/export_sweep_workfiles.py

Exporta los tres archivos de trabajo para la campaña de data entry:

  staging/inversores_sin_edges.csv    — Carril A: fondos inactivos para sweep
  staging/edges_sin_source.csv        — Carril C: edges a las que falta source_url
  staging/capital_intake.csv          — Template vacío para agregar edges nuevas

Uso:
  python scripts/export_sweep_workfiles.py
"""
from __future__ import annotations

import csv
import pathlib
import sqlite3
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT    = pathlib.Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "db" / "bio_latam.db"
STAGING = ROOT / "staging"


def export_inversores_sin_edges(conn: sqlite3.Connection) -> int:
    """Carril A: inversores registrados sin ninguna edge."""
    rows = conn.execute("""
        SELECT i.investor_id, e.canonical_name AS investor_name,
               i.investor_type, e.website, e.country_code,
               i.geography_focus, i.vertical_focus,
               i.thesis
        FROM investors i
        JOIN entities e ON e.entity_id = i.investor_id
        WHERE i.investor_id NOT IN (
            SELECT DISTINCT investor_id FROM investment_edges
        )
        ORDER BY
          CASE i.investor_type
            WHEN 'vc'                  THEN 1
            WHEN 'impact_fund'         THEN 2
            WHEN 'accelerator'         THEN 3
            WHEN 'corporate_vc'        THEN 4
            WHEN 'multilateral'        THEN 5
            WHEN 'development_finance' THEN 6
            ELSE 9
          END,
          e.canonical_name
    """).fetchall()

    out = STAGING / "inversores_sin_edges.csv"
    COLS = [
        "investor_id", "investor_name", "investor_type",
        "website", "country_code", "geography_focus", "vertical_focus",
        "thesis",
        # Columnas de trabajo para el curador:
        "sweep_status",   # pending / done / skip
        "portfolio_url",  # URL revisada de portfolio
        "edges_found",    # número de edges encontradas
        "notes_curador",  # observaciones
    ]
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        for r in rows:
            w.writerow([
                r[0], r[1], r[2], r[3] or "", r[4] or "",
                r[5] or "", r[6] or "", r[7] or "",
                "pending", "", "", "",
            ])
    return len(rows)


def export_edges_sin_source(conn: sqlite3.Connection) -> int:
    """Carril C: edges con source_id NULL."""
    rows = conn.execute("""
        SELECT ie.investment_id, ie.investor_id,
               ei.canonical_name AS investor_name,
               ie.startup_id,
               es.canonical_name AS startup_name,
               sx.bio_theme_primary AS bio_theme,
               ie.round_stage, ie.round_name,
               ie.confidence_score, ie.notes
        FROM investment_edges ie
        JOIN entities ei ON ei.entity_id = ie.investor_id
        JOIN entities es ON es.entity_id = ie.startup_id
        LEFT JOIN startup_extended sx ON sx.startup_id = ie.startup_id
        WHERE ie.source_id IS NULL
        ORDER BY ie.investor_id, ie.startup_id
    """).fetchall()

    out = STAGING / "edges_sin_source.csv"
    COLS = [
        "investment_id", "investor_id", "investor_name",
        "startup_id", "startup_name", "bio_theme",
        "round_stage", "round_name", "confidence_score",
        "notes_originales",
        # Columnas de trabajo:
        "source_url_recuperada",  # curador llena
        "accion",                 # keep_with_url / downgrade_confidence / discard
    ]
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        for r in rows:
            w.writerow([
                r[0], r[1], r[2], r[3], r[4], r[5] or "",
                r[6] or "", r[7] or "", r[8], r[9] or "",
                "", "keep_with_url",
            ])
    return len(rows)


def export_intake_template() -> None:
    """Template vacío para agregar edges nuevas en cada sesión de sweep."""
    out = STAGING / "capital_intake.csv"

    # Si ya existe con datos, no sobreescribir — solo crear si vacío o inexistente
    if out.exists():
        with out.open("r", encoding="utf-8-sig") as f:
            content = f.read().strip()
        lines = [l for l in content.splitlines() if l.strip()]
        if len(lines) > 1:  # tiene datos además del header
            print(f"  capital_intake.csv ya tiene datos — no se sobreescribe.")
            print(f"  Agregar nuevas filas al final del archivo existente.")
            return

    COLS = [
        # Identificadores (al menos uno de cada par es requerido)
        "investor_id",      # slug canónico (ej: sp_ventures) — preferido
        "investor_name",    # nombre libre si no se conoce el slug
        "startup_id",       # slug canónico (ej: bioceres) — preferido
        "startup_name",     # nombre libre si no se conoce el slug
        # Clasificación
        "round_stage",      # pre-seed | seed | series-a | series-b | series-c | growth
        "round_name",       # nombre libre (ej: "Serie A USD 5M")
        "announced_date",   # YYYY-MM-DD o YYYY-MM o YYYY
        "amount_usd",       # número sin símbolo (ej: 5000000)
        "currency",         # USD (default) | BRL | CLP | COP | MXN | ARS
        "is_lead",          # 1 si es lead investor, 0 si no, vacío si desconocido
        # Evidencia (OBLIGATORIO al menos source_url)
        "source_url",       # URL pública de la evidencia — REQUERIDO
        "confidence_score", # 0.90 (portfolio page) | 0.95 (startup-specific) | 0.98 (press release)
        "notes",            # descripción breve de la relación y evidencia
    ]

    # Fila de ejemplo comentada como guía
    example = [
        "sp_ventures",
        "",
        "biome_makers",
        "",
        "series-a",
        "Serie A liderada por SP Ventures",
        "2023-06",
        "3000000",
        "USD",
        "1",
        "https://spventures.com.br/portfolio/biome-makers",
        "0.96",
        "SP Ventures portfolio page lista Biome Makers como portfolio company",
    ]

    with out.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        w.writerow(example)  # Fila de ejemplo
        # 10 filas vacías para que el curador vea la estructura en Excel
        for _ in range(10):
            w.writerow([""] * len(COLS))


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    STAGING.mkdir(parents=True, exist_ok=True)

    n_inv  = export_inversores_sin_edges(conn)
    n_edge = export_edges_sin_source(conn)
    export_intake_template()

    conn.close()

    print(f"\n  Archivos exportados a staging/:")
    print(f"  inversores_sin_edges.csv   — {n_inv} fondos para sweep (Carril A)")
    print(f"  edges_sin_source.csv       — {n_edge} edges sin trazabilidad (Carril C)")
    print(f"  capital_intake.csv         — template para agregar edges nuevas")
    print()
    print("  Workflow:")
    print("  1. Abre inversores_sin_edges.csv — visita portfolio page de cada fondo")
    print("  2. Por cada startup encontrada: agrega fila en capital_intake.csv")
    print("  3. Cuando termines un lote:")
    print("     python scripts/intake_to_canonical.py  # convierte intake → canonical")
    print("     python pipeline.py rebuild --phase canonical")
    print("     python pipeline.py build-atlas")
    print()


if __name__ == "__main__":
    main()
