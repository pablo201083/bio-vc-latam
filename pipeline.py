"""
pipeline.py — Entry point único del BIO LATAM Ecosystem Tracker.

Uso:
    python pipeline.py status                   # counts por tabla
    python pipeline.py validate                 # validaciones de integridad
    python pipeline.py ingest-founding-years    # staging/founding_years.csv → entities
    python pipeline.py ingest-rounds            # staging/investment_rounds.csv → investment_edges
    python pipeline.py ingest-outcomes          # staging/outcomes_incoming.csv → outcomes
    python pipeline.py rebuild                  # rebuild completo del dashboard JS
    python pipeline.py rebuild --phase semantic # solo fase semántica (embeddings + clustering)
    python pipeline.py graph --refresh          # PageRank / communities / bridges
"""
from __future__ import annotations

import argparse
import io
import sqlite3
import sys
from pathlib import Path

# Fix Windows cp1252 terminal encoding
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf-8-sig"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent
DB_PATH = ROOT / "db" / "bio_latam.db"

sys.path.insert(0, str(ROOT))


# ──────────────────────────────────────────────
# status
# ──────────────────────────────────────────────

def cmd_status(args: argparse.Namespace) -> None:
    conn = sqlite3.connect(DB_PATH)
    print(f"\n{'='*52}")
    print(f"  BIO LATAM DB -- {DB_PATH.name}")
    print(f"{'='*52}")

    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()

    for (t,) in tables:
        n = conn.execute(f"SELECT count(*) FROM [{t}]").fetchone()[0]
        bar = "█" * min(n // 10, 30) if n > 0 else "·"
        print(f"  {t:<35} {n:>5}  {bar}")

    print(f"{'='*52}")

    # Resumen operativo
    try:
        inc = conn.execute(
            "SELECT count(*) FROM startup_extended WHERE scope_decision='include'"
        ).fetchone()[0]
        edges = conn.execute("SELECT count(*) FROM investment_edges").fetchone()[0]
        with_rounds = conn.execute(
            "SELECT count(*) FROM investment_edges WHERE round_stage IS NOT NULL"
        ).fetchone()[0]
        outcomes = conn.execute("SELECT count(*) FROM outcomes").fetchone()[0]
        audit = conn.execute("SELECT count(*) FROM audit_log").fetchone()[0]
        orphans = conn.execute(
            "SELECT count(*) FROM entities WHERE entity_type='startup' "
            "AND NOT EXISTS (SELECT 1 FROM startup_extended sx WHERE sx.startup_id=entity_id)"
        ).fetchone()[0]

        print(f"\n  Startups include      : {inc}")
        print(f"  Investment edges      : {edges} ({with_rounds} con round_stage)")
        print(f"  Outcomes registrados  : {outcomes}")
        print(f"  Audit log entries     : {audit}")
        print(f"  Orphan entities       : {orphans} (sin startup_extended)")
    except Exception as e:
        print(f"  [warn] resumen parcial: {e}")

    print()
    conn.close()


# ──────────────────────────────────────────────
# validate
# ──────────────────────────────────────────────

def cmd_validate(args: argparse.Namespace) -> None:
    conn = sqlite3.connect(DB_PATH)
    errors = 0
    warnings = 0

    print(f"\n  Validaciones de integridad — {DB_PATH.name}\n")

    checks = [
        # (descripción, query, tipo)
        (
            "Startups include sin startup_summary_v1",
            "SELECT count(*) FROM startup_extended WHERE scope_decision='include' "
            "AND (startup_summary_v1 IS NULL OR startup_summary_v1='')",
            "warn",
        ),
        (
            "Startups include sin macro_theme",
            "SELECT count(*) FROM startup_extended WHERE scope_decision='include' "
            "AND (macro_theme IS NULL OR macro_theme='')",
            "error",
        ),
        (
            "Startups include sin country_code en entities",
            "SELECT count(*) FROM entities e JOIN startup_extended sx ON e.entity_id=sx.startup_id "
            "WHERE sx.scope_decision='include' AND (e.country_code IS NULL OR e.country_code='')",
            "warn",
        ),
        (
            "Investment edges con investor_id inexistente",
            "SELECT count(*) FROM investment_edges ie WHERE NOT EXISTS "
            "(SELECT 1 FROM entities e WHERE e.entity_id=ie.investor_id)",
            "error",
        ),
        (
            "Investment edges con startup_id inexistente",
            "SELECT count(*) FROM investment_edges ie WHERE NOT EXISTS "
            "(SELECT 1 FROM entities e WHERE e.entity_id=ie.startup_id)",
            "error",
        ),
        (
            "Outcomes sin source_url",
            "SELECT count(*) FROM outcomes WHERE source_url IS NULL OR source_url=''",
            "error",
        ),
        (
            "Startups include sin tech_codes ni industry_codes",
            "SELECT count(*) FROM startup_extended WHERE scope_decision='include' "
            "AND (tech_codes IS NULL OR tech_codes='[]') "
            "AND (industry_codes IS NULL OR industry_codes='[]')",
            "warn",
        ),
        (
            "Orphan entities (sin startup_extended)",
            "SELECT count(*) FROM entities WHERE entity_type='startup' "
            "AND NOT EXISTS (SELECT 1 FROM startup_extended sx WHERE sx.startup_id=entity_id)",
            "info",
        ),
    ]

    for desc, query, level in checks:
        try:
            n = conn.execute(query).fetchone()[0]
            icon = {"error": "X", "warn": "!", "info": "-"}.get(level, "-")
            status = "OK" if n == 0 else str(n)
            print(f"  {icon} {desc:<55} {status}")
            if n > 0:
                if level == "error":
                    errors += 1
                elif level == "warn":
                    warnings += 1
        except Exception as e:
            print(f"  ? {desc:<55} ERROR: {e}")
            errors += 1

    print()
    if errors:
        print(f"  {errors} error(s), {warnings} warning(s)\n")
        sys.exit(1)
    else:
        print(f"  OK — {warnings} warning(s)\n")

    conn.close()


# ──────────────────────────────────────────────
# ingest-founding-years
# ──────────────────────────────────────────────

def cmd_ingest_founding_years(args: argparse.Namespace) -> None:
    from src.ingest import ingest_founding_years
    print("\n  Ingesting founding years...\n")
    stats = ingest_founding_years(DB_PATH)
    print(f"\n  Resultado: {stats}\n")


# ──────────────────────────────────────────────
# ingest-rounds
# ──────────────────────────────────────────────

def cmd_ingest_rounds(args: argparse.Namespace) -> None:
    from src.ingest import ingest_rounds
    print("\n  Ingesting investment rounds...\n")
    stats = ingest_rounds(DB_PATH)
    print(f"\n  Resultado: {stats}\n")


# ──────────────────────────────────────────────
# ingest-outcomes
# ──────────────────────────────────────────────

def cmd_ingest_outcomes(args: argparse.Namespace) -> None:
    from src.ingest import ingest_outcomes
    print("\n  Ingesting outcomes...\n")
    stats = ingest_outcomes(DB_PATH)
    print(f"\n  Resultado: {stats}\n")


# ──────────────────────────────────────────────
# rebuild
# ──────────────────────────────────────────────

def cmd_rebuild(args: argparse.Namespace) -> None:
    phase = getattr(args, "phase", None)
    print(f"\n  Rebuild{f' --phase {phase}' if phase else ' (completo)'}...\n")

    if phase in (None, "semantic", "embeddings"):
        try:
            from src.embeddings import run as run_embeddings
            print("  [embeddings] generando vectores...")
            run_embeddings(ROOT, DB_PATH)
        except Exception as e:
            print(f"  [embeddings] ERROR: {e}")

    if phase in (None, "semantic", "clustering"):
        try:
            from src.clustering import write_dashboard_data
            print("  [clustering] calculando clusters + escribiendo JS...")
            write_dashboard_data(str(DB_PATH), str(ROOT / "pilot" / "startup-themes-data.js"))
            print("  [clustering] OK → pilot/startup-themes-data.js")
        except Exception as e:
            print(f"  [clustering] ERROR: {e}")

    print()


# ──────────────────────────────────────────────
# graph --refresh
# ──────────────────────────────────────────────

def cmd_graph(args: argparse.Namespace) -> None:
    refresh = getattr(args, "refresh", False)
    if not refresh:
        print("  Usa: python pipeline.py graph --refresh")
        return
    try:
        from src.graph_analytics import run as run_graph
        print("\n  Calculando PageRank / communities / bridges...\n")
        run_graph(ROOT, DB_PATH)
        print("  OK\n")
    except Exception as e:
        print(f"  [graph] ERROR: {e}\n")


# ──────────────────────────────────────────────
# CLI main
# ──────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pipeline",
        description="BIO LATAM Ecosystem Tracker — pipeline de datos",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Counts por tabla")
    sub.add_parser("validate", help="Validaciones de integridad")
    sub.add_parser("ingest-founding-years", help="staging/founding_years.csv → entities.founded_year")
    sub.add_parser("ingest-rounds", help="staging/investment_rounds.csv → investment_edges")
    sub.add_parser("ingest-outcomes", help="staging/outcomes_incoming.csv → outcomes")

    rb = sub.add_parser("rebuild", help="Rebuild completo o por fase")
    rb.add_argument(
        "--phase",
        choices=["semantic", "embeddings", "clustering"],
        help="Solo una fase del rebuild",
    )

    gp = sub.add_parser("graph", help="Calcular métricas de grafo")
    gp.add_argument("--refresh", action="store_true", help="Forzar recálculo")

    args = parser.parse_args()

    dispatch = {
        "status": cmd_status,
        "validate": cmd_validate,
        "ingest-founding-years": cmd_ingest_founding_years,
        "ingest-rounds": cmd_ingest_rounds,
        "ingest-outcomes": cmd_ingest_outcomes,
        "rebuild": cmd_rebuild,
        "graph": cmd_graph,
    }

    fn = dispatch.get(args.command)
    if fn:
        fn(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
