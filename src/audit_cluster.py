"""
src/audit_cluster.py — Proceso de auditoría y clustering integrado.

Workflow end-to-end:
  1. Identifica startups con data gaps críticos
  2. Genera reporte de auditoría (triage CSV)
  3. Permite curation manual de datos
  4. Re-ejecuta clustering semántico
  5. Compara clusters antes/después
  6. Registra cambios en audit_log

Uso:
    python pipeline.py audit-and-cluster                   # generar triage
    python pipeline.py audit-and-cluster --apply-fix       # re-cluster tras curation
"""
from __future__ import annotations

import pathlib
import sqlite3
import csv
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Campos críticos que deben estar completos para que el clustering sea confiable
CRITICAL_FIELDS = {
    "funding_stage": "Etapa de financiamiento",
    "computed_quality_score": "Puntuación de calidad",
    "tech_depth": "Profundidad tecnológica",
    "short_description": "Descripción corta",
}

# Campos recomendados
RECOMMENDED_FIELDS = {
    "website": "Sitio web",
    "founded_year": "Año de fundación",
}


def _identify_gaps(conn: sqlite3.Connection) -> list[dict]:
    """Identifica startups con data gaps críticos."""
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Startups include con gaps críticos
    cursor.execute("""
    SELECT sx.startup_id, e.canonical_name, sx.bio_theme_primary,
           sx.cluster_id, sx.cluster_label, sx.sub_cluster_label,
           sx.funding_stage, sx.computed_quality_score, sx.tech_depth,
           e.short_description, e.website, e.founded_year
    FROM startup_extended sx
    JOIN entities e ON e.entity_id = sx.startup_id
    WHERE sx.scope_decision = 'include'
      AND (sx.funding_stage IS NULL OR sx.funding_stage = ''
           OR sx.computed_quality_score IS NULL
           OR sx.tech_depth IS NULL OR sx.tech_depth = ''
           OR e.short_description IS NULL OR e.short_description = '')
    ORDER BY e.canonical_name
    """)

    gaps = []
    for row in cursor.fetchall():
        missing_critical = []
        missing_recommended = []

        if not row['funding_stage']:
            missing_critical.append("funding_stage")
        if row['computed_quality_score'] is None:
            missing_critical.append("computed_quality_score")
        if not row['tech_depth']:
            missing_critical.append("tech_depth")
        if not row['short_description']:
            missing_critical.append("short_description")

        if not row['website']:
            missing_recommended.append("website")
        if not row['founded_year']:
            missing_recommended.append("founded_year")

        gaps.append({
            "startup_id": row['startup_id'],
            "name": row['canonical_name'],
            "bio_theme": row['bio_theme_primary'],
            "cluster_id": row['cluster_id'],
            "cluster_label": row['cluster_label'],
            "sub_cluster_label": row['sub_cluster_label'],
            "missing_critical": missing_critical,
            "missing_recommended": missing_recommended,
            "severity": "high" if len(missing_critical) >= 3 else "medium",
        })

    conn.row_factory = None
    return gaps


def run_audit(db_path: pathlib.Path) -> dict:
    """Ejecuta auditoría y genera triage CSV."""
    conn = sqlite3.connect(db_path)

    gaps = _identify_gaps(conn)
    conn.close()

    # Generar CSV de triage
    triage_path = ROOT / "quality" / "audit_cluster_triage.csv"
    with open(triage_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "startup_id", "name", "bio_theme", "cluster_id", "cluster_label",
                "sub_cluster_label", "severity", "missing_critical", "missing_recommended",
                "curation_status", "notes"
            ]
        )
        writer.writeheader()
        for gap in gaps:
            writer.writerow({
                "startup_id": gap["startup_id"],
                "name": gap["name"],
                "bio_theme": gap["bio_theme"],
                "cluster_id": gap["cluster_id"],
                "cluster_label": gap["cluster_label"],
                "sub_cluster_label": gap["sub_cluster_label"],
                "severity": gap["severity"],
                "missing_critical": " | ".join(gap["missing_critical"]),
                "missing_recommended": " | ".join(gap["missing_recommended"]),
                "curation_status": "pending",
                "notes": ""
            })

    # Resumen
    high_severity = sum(1 for g in gaps if g["severity"] == "high")
    medium_severity = sum(1 for g in gaps if g["severity"] == "medium")

    return {
        "total_gaps": len(gaps),
        "high_severity": high_severity,
        "medium_severity": medium_severity,
        "triage_output": str(triage_path),
        "gaps_by_theme": {},
    }


def run(db_path: pathlib.Path, apply_fix: bool = False) -> None:
    """Punto de entrada del comando audit-and-cluster."""

    if not apply_fix:
        # Modo auditoría: generar triage
        print("\n  Auditando startups con data gaps...\n")
        result = run_audit(db_path)

        print(f"  Total gaps detectados: {result['total_gaps']}")
        print(f"    High severity: {result['high_severity']}")
        print(f"    Medium severity: {result['medium_severity']}")
        print(f"\n  Triage CSV: {result['triage_output']}")
        print(f"\n  Próximo paso:")
        print(f"    1. Editar {result['triage_output']}")
        print(f"    2. Completar datos en entities/startup_extended")
        print(f"    3. Ejecutar: python pipeline.py audit-and-cluster --apply-fix")
        print()
    else:
        # Modo aplicar fix: re-ejecutar clustering
        print("\n  Re-ejecutando clustering tras curation...\n")
        from src.clustering import run as run_clustering

        conn = sqlite3.connect(db_path)
        print("  [clustering] Ejecutando UMAP + HDBSCAN...")
        run_clustering(db_path)

        print("\n  Clustering completado.")
        print("  Ver cambios en: pilot/startup-themes-data.js")
        print()
