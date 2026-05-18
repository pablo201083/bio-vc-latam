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

GRAPH_REFRESH_MIN_CHANGES = 10


def _maybe_refresh_graph(stats: dict, args: argparse.Namespace) -> None:
    """Corre graph analytics si --graph-refresh y cambios >= GRAPH_REFRESH_MIN_CHANGES."""
    if not getattr(args, "graph_refresh", False):
        return
    total = stats.get("updated", 0) + stats.get("created", 0) + stats.get("inserted", 0)
    if total >= GRAPH_REFRESH_MIN_CHANGES:
        try:
            from src.graph_analytics import run as run_graph
            print(f"\n  [--graph-refresh] {total} cambios → recalculando grafo...\n")
            run_graph(DB_PATH)
        except Exception as e:
            print(f"  [graph-refresh] ERROR: {e}")
    else:
        print(f"  [--graph-refresh] solo {total} cambios < {GRAPH_REFRESH_MIN_CHANGES} — skip")


def cmd_ingest_rounds(args: argparse.Namespace) -> None:
    from src.ingest import ingest_rounds
    print("\n  Ingesting investment rounds...\n")
    stats = ingest_rounds(DB_PATH)
    print(f"\n  Resultado: {stats}\n")
    _maybe_refresh_graph(stats, args)


# ──────────────────────────────────────────────
# ingest-outcomes
# ──────────────────────────────────────────────

def cmd_ingest_outcomes(args: argparse.Namespace) -> None:
    from src.ingest import ingest_outcomes
    print("\n  Ingesting outcomes...\n")
    stats = ingest_outcomes(DB_PATH)
    print(f"\n  Resultado: {stats}\n")


# ──────────────────────────────────────────────
# translate
# ──────────────────────────────────────────────

def cmd_translate(args: argparse.Namespace) -> None:
    from src.translate import run as run_translate
    force = getattr(args, "force", False)
    print(f"\n  {'[FORCE] ' if force else ''}Translating summaries to English...\n")
    stats = run_translate(DB_PATH, force=force)
    print(f"\n  Result: {stats}\n")


# ──────────────────────────────────────────────
# ingest-discovered
# ──────────────────────────────────────────────

def cmd_ingest_discovered(args: argparse.Namespace) -> None:
    from src.discovery import ingest_discovered
    print("\n  Ingesting discovered startups...\n")
    stats = ingest_discovered(DB_PATH)
    print(f"\n  Resultado: {stats}\n")
    _maybe_refresh_graph(stats, args)


def cmd_dedup_investment_edges(args: argparse.Namespace) -> None:
    from src.ingest import dedup_investment_edges
    print("\n  Deduplicating investment edges...\n")
    stats = dedup_investment_edges(DB_PATH)
    print(f"\n  Resultado: {stats}\n")


def cmd_merge_duplicate_entities(args: argparse.Namespace) -> None:
    from src.ingest import merge_duplicate_entities
    dry = getattr(args, "dry_run", False)
    print(f"\n  {'[DRY RUN] ' if dry else ''}Merging duplicate entities...\n")
    stats = merge_duplicate_entities(DB_PATH, dry_run=dry)
    print(f"\n  Resultado: {stats}\n")


# ──────────────────────────────────────────────
# ingest-fund-profiles
# ──────────────────────────────────────────────

def cmd_ingest_fund_profiles(args: argparse.Namespace) -> None:
    from src.ingest import ingest_fund_profiles
    print("\n  Ingesting fund profiles (enriquecimiento de inversores)...\n")
    stats = ingest_fund_profiles(DB_PATH)
    print(f"\n  Resultado: {stats}\n")


# ──────────────────────────────────────────────
# ingest-entity-enrichments
# ──────────────────────────────────────────────

def cmd_ingest_entity_enrichments(args: argparse.Namespace) -> None:
    from src.ingest import ingest_entity_enrichments
    print("\n  Ingesting entity enrichments (correcciones masivas de campos)...\n")
    stats = ingest_entity_enrichments(DB_PATH)
    print(f"\n  Resultado: {stats}\n")


# ──────────────────────────────────────────────
# ingest-new-investors
# ──────────────────────────────────────────────

def cmd_ingest_new_investors(args: argparse.Namespace) -> None:
    from src.ingest_funds import ingest_new_investors
    print("\n  Ingesting new investors (entidades nuevas de fondos)...\n")
    stats = ingest_new_investors(DB_PATH)
    print(f"\n  Resultado: {stats}\n")


# ──────────────────────────────────────────────
# ingest-capital-allocators
# ──────────────────────────────────────────────

def cmd_ingest_capital_allocators(args: argparse.Namespace) -> None:
    from src.ingest_funds import ingest_capital_allocators
    print("\n  Ingesting capital allocator relationships (LP→fondo)...\n")
    stats = ingest_capital_allocators(DB_PATH)
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
            from src.clustering import run as run_clustering
            print("  [clustering] UMAP + HDBSCAN + dashboard JS...")
            run_clustering(DB_PATH)
            print("  [clustering] OK => pilot/startup-themes-data.js")
        except Exception as e:
            print(f"  [clustering] ERROR: {e}")

    print()


# ──────────────────────────────────────────────
# graph --refresh
# ──────────────────────────────────────────────

def cmd_reclassify(args: argparse.Namespace) -> None:
    from src.reclassify import run as run_reclassify, THEME_NAMES
    dry = getattr(args, "dry_run", False)
    print(f"\n  {'[DRY RUN] ' if dry else ''}Reclassifying bio themes...\n")
    stats, results = run_reclassify(DB_PATH, dry_run=dry)
    print(f"\n  {'='*52}")
    print(f"  Total classified : {stats['total']}")
    print(f"  Bio-core         : {stats['bio_core']}")
    print(f"  Eco-adjacent     : {stats['eco_adjacent']}")
    print(f"  Unclassified     : {stats['unclassified']}")
    print(f"\n  By theme:")
    for theme, n in stats["by_theme"].items():
        bar = "█" * min(n, 30)
        print(f"    {theme:<42} {n:>4}  {bar}")
    print(f"  {'='*52}\n")
    if dry:
        print("  [dry-run] Showing 20 samples:\n")
        for r in sorted(results, key=lambda x: x["name"])[:20]:
            sec = f" / {r['secondary']}" if r["secondary"] else ""
            bio = "BIO" if r["is_bio"] else "ADJ"
            print(f"    [{bio}] {r['name']:<40} {r['primary']}{sec}")
        print()


def cmd_quality_report(args: argparse.Namespace) -> None:
    from src.quality_report import run as run_quality
    output = ROOT / "pilot" / "quality-tracker.html"
    print("\n  Generating Quality Tracker...\n")
    run_quality(DB_PATH, output)
    print(f"\n  Done => pilot/quality-tracker.html\n")


def cmd_enrich_rounds_valuation(args: argparse.Namespace) -> None:
    from src.ingest import enrich_rounds_from_valuation_tier
    print("\n  Phase D Pass 1 — Inferir round_stage desde valuation_tier...\n")
    stats = enrich_rounds_from_valuation_tier(DB_PATH)
    print(f"\n  Resultado: {stats}\n")


def cmd_build_atlas(args: argparse.Namespace) -> None:
    from src.capital_atlas import run as run_atlas
    print("\n  Building Capital Network Atlas data...\n")
    stats = run_atlas(DB_PATH)
    print(f"\n  Summary: {stats}\n")


def cmd_fund_sweep_status(args: argparse.Namespace) -> None:
    from scripts.capital_sweep_status import run as run_status
    run_status(DB_PATH)


def cmd_graph(args: argparse.Namespace) -> None:
    refresh = getattr(args, "refresh", False)
    if not refresh:
        print("  Usa: python pipeline.py graph --refresh")
        return
    try:
        from src.graph_analytics import run as run_graph
        print("\n  Calculando PageRank / communities / bridges...\n")
        run_graph(DB_PATH)
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
    ir = sub.add_parser("ingest-rounds", help="staging/investment_rounds.csv → investment_edges")
    ir.add_argument("--graph-refresh", action="store_true", help=f"Recalcular grafo si >= {GRAPH_REFRESH_MIN_CHANGES} cambios")
    sub.add_parser("ingest-outcomes", help="staging/outcomes_incoming.csv → outcomes")
    tr = sub.add_parser("translate", help="Normalize startup_summary_v1 → startup_summary_en (English)")
    tr.add_argument("--force", action="store_true", help="Retranslate even already-translated summaries")

    disc = sub.add_parser("ingest-discovered", help="staging/discovered_startups.csv → entities + startup_extended")
    disc.add_argument("--graph-refresh", action="store_true", help=f"Recalcular grafo si >= {GRAPH_REFRESH_MIN_CHANGES} cambios")
    sub.add_parser("ingest-fund-profiles", help="staging/fund_profiles.csv → enriquecer investors + entities")
    sub.add_parser("ingest-entity-enrichments", help="staging/entity_enrichments.csv → correcciones masivas de campos")
    sub.add_parser("ingest-new-investors", help="staging/new_investors.csv → crear entidades nuevas de fondos")
    sub.add_parser("ingest-capital-allocators", help="quality/capital_allocator_edges.csv → capital_relations (LP→fondo)")
    sub.add_parser("enrich-rounds-valuation", help="Phase D Pass 1 — inferir round_stage desde valuation_tier (confidence=0.5)")
    sub.add_parser("dedup-investment-edges", help="Eliminar edges duplicadas (mismo investor+startup) — mantiene la de mayor prioridad")
    mde = sub.add_parser("merge-duplicate-entities", help="CRITICO: migrar edges de entity_ids duplicados (PascalCase) al canonical slug con startup_extended")
    mde.add_argument("--dry-run", action="store_true", help="Ver pares sin modificar DB")
    sub.add_parser("build-atlas", help="Regenerar pilot/capital-atlas-data.js desde SQLite (investment_edges + capital_relations)")
    sub.add_parser("fund-sweep-status", help="Dashboard de cobertura del grafo de capital + guía para el sweep")
    sub.add_parser("quality-report", help="Genera pilot/quality-tracker.html con métricas de calidad")

    rc = sub.add_parser("reclassify-themes", help="Asigna bio_theme_primary/secondary + is_bio_universe a todos los includes")
    rc.add_argument("--dry-run", action="store_true", help="Muestra resultados sin escribir al DB")

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
        "translate": cmd_translate,
        "ingest-discovered": cmd_ingest_discovered,
        "ingest-fund-profiles": cmd_ingest_fund_profiles,
        "ingest-entity-enrichments": cmd_ingest_entity_enrichments,
        "ingest-new-investors": cmd_ingest_new_investors,
        "ingest-capital-allocators": cmd_ingest_capital_allocators,
        "enrich-rounds-valuation": cmd_enrich_rounds_valuation,
        "dedup-investment-edges": cmd_dedup_investment_edges,
        "merge-duplicate-entities": cmd_merge_duplicate_entities,
        "build-atlas": cmd_build_atlas,
        "fund-sweep-status": cmd_fund_sweep_status,
        "quality-report": cmd_quality_report,
        "reclassify-themes": cmd_reclassify,
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
