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

    # ── Spatial & semantic consistency checks (require Python math) ──────────
    print("  ── Consistencia semántica ──────────────────────────────────────────")
    import math, statistics as _stats

    rows = conn.execute("""
        SELECT e.entity_id, e.canonical_name, sx.bio_theme_primary,
               sx.cluster_label, sx.umap_x, sx.umap_y, sx.data_quality_score
        FROM startup_extended sx
        JOIN entities e ON e.entity_id = sx.startup_id
        WHERE sx.scope_decision = 'include'
          AND sx.umap_x IS NOT NULL
    """).fetchall()

    # 1. bio_theme vs cluster_label: solo los conflictos GENUINOS cuentan.
    #    Un bio_theme que forma subgrupo coherente dentro de un cluster grueso
    #    (o un tema transversal disperso) NO es contradicción — es sub-cluster.
    #    Fuente de verdad única: src.reconcile_themes.analyze (Frente B).
    from src.reconcile_themes import analyze as _analyze_conflicts
    triage = _analyze_conflicts(conn)
    isolated = [t for t in triage if t["verdict"] == "isolated_review"]
    n_expected = len(triage) - len(isolated)
    n_mm = len(isolated)
    icon = "!" if n_mm > 0 else " "
    print(f"  {icon} {'bio_theme ≠ cluster_label (conflictos aislados)':<55} {n_mm if n_mm else 'OK'}")
    print(f"    {'(+ sub-cluster/transversal esperados, no error)':<55} {n_expected}")
    if n_mm > 0:
        for t in isolated[:5]:
            print(f"      {t['name'][:36]:<36} [{t['bio_theme'][:24]}] en cluster [{t['cluster_label_prefix'][:22]}]")
        if n_mm > 5:
            print(f"      … y {n_mm - 5} más → quality/theme_cluster_mismatch_triage.csv")
        warnings += 1

    # 2. Positional outliers — distancia al centroide del bio_theme
    theme_pts: dict = {}
    for r in rows:
        t = r[2]
        if t:
            theme_pts.setdefault(t, []).append((r[4], r[5]))
    centroids = {
        t: (_stats.mean(p[0] for p in pts), _stats.mean(p[1] for p in pts))
        for t, pts in theme_pts.items()
    }
    DIST_THRESHOLD = 5.0
    outliers = []
    for r in rows:
        t = r[2]
        if t and t in centroids:
            cx, cy = centroids[t]
            d = math.sqrt((r[4] - cx) ** 2 + (r[5] - cy) ** 2)
            if d > DIST_THRESHOLD:
                outliers.append((r[1], t, round(d, 1), r[6] or 0))
    outliers.sort(key=lambda x: -x[2])
    n_out = len(outliers)
    icon = "!" if n_out > 0 else " "
    print(f"  {icon} {f'UMAP: startups a distancia > {DIST_THRESHOLD} del centroide de su tema':<55} {n_out if n_out else 'OK'}")
    if n_out > 0:
        for nm, theme, d, q in outliers[:5]:
            print(f"      {nm:<38} {theme[:32]}  d={d}  q={q:.0f}")
        if n_out > 5:
            print(f"      … y {n_out - 5} más")
        warnings += 1

    # 3. Empresas con quality=0 en clusters metodológicos (alta diversidad temática)
    cl_theme_count: dict = {}
    for r in rows:
        cid = conn.execute(
            "SELECT cluster_id FROM startup_extended WHERE startup_id=?", (r[0],)
        ).fetchone()
        if cid:
            cl_theme_count.setdefault(cid[0], set()).add(r[2])
    diverse_clusters = {cid for cid, themes in cl_theme_count.items() if len(themes) >= 3}
    q0_diverse = [
        r[1] for r in rows
        if (r[6] or 0) == 0.0
        and conn.execute(
            "SELECT cluster_id FROM startup_extended WHERE startup_id=?", (r[0],)
        ).fetchone()[0] in diverse_clusters
    ]
    n_q0d = len(q0_diverse)
    icon = "!" if n_q0d > 0 else " "
    print(f"  {icon} {'quality=0 en clusters metodológicos (≥3 temas mezclados)':<55} {n_q0d if n_q0d else 'OK'}")
    if n_q0d > 0:
        for nm in q0_diverse[:5]:
            print(f"      {nm}")
        if n_q0d > 5:
            print(f"      … y {n_q0d - 5} más")
        warnings += 1

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


def cmd_ingest_intake(args: argparse.Namespace) -> None:
    """staging/capital_intake.csv → canonical → investment_edges → build-atlas."""
    import csv, subprocess
    intake_file = getattr(args, "file", None)
    dry = getattr(args, "dry_run", False)

    # Step 1: intake_to_canonical.py convierte staging CSV → manual_canonical_investment_edges.csv
    cmd = [sys.executable, "scripts/intake_to_canonical.py"]
    if intake_file:
        cmd += ["--file", str(intake_file)]
    if dry:
        cmd += ["--dry-run"]
    print("\n  ── Step 1: intake → manual_canonical ───────────────────────")
    result = subprocess.run(cmd, cwd=str(ROOT))
    if result.returncode != 0 or dry:
        if dry:
            print("\n  [dry-run] Nada escrito — stopping.")
        return

    # Step 2: manual_canonical_investment_edges.csv → investment_edges
    print("\n  ── Step 2: canonical → investment_edges ────────────────────")
    canonical_path = ROOT / "canonical" / "manual_canonical_investment_edges.csv"
    if not canonical_path.exists():
        print(f"  [ERROR] {canonical_path} no existe")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")

    with canonical_path.open("r", encoding="utf-8-sig") as f:
        can_rows = list(csv.DictReader(f))

    created = skipped = errors = 0
    for row in can_rows:
        inv_id = (row.get("investor_id_candidate") or "").strip()
        sta_id = (row.get("startup_id_candidate") or "").strip()
        edge_id = (row.get("raw_edge_id") or "").strip()
        if not inv_id or not sta_id or not edge_id:
            continue

        # Skip if already exists
        exists = conn.execute(
            "SELECT 1 FROM investment_edges WHERE investor_id=? AND startup_id=?",
            (inv_id, sta_id),
        ).fetchone()
        if exists:
            skipped += 1
            continue

        # Verify entities exist
        inv_ok = conn.execute("SELECT 1 FROM entities WHERE entity_id=?", (inv_id,)).fetchone()
        sta_ok = conn.execute("SELECT 1 FROM entities WHERE entity_id=?", (sta_id,)).fetchone()
        if not inv_ok or not sta_ok:
            print(f"  [warn] entidad no encontrada: {inv_id if not inv_ok else sta_id} — skip")
            errors += 1
            continue

        conf = float(row.get("confidence_score") or 0.9)
        src_url = (row.get("source_file") or "").strip()
        notes = (row.get("notes") or "").strip()
        rel = (row.get("relation_type_raw") or "official_portfolio_investment").strip()

        conn.execute("""
            INSERT INTO investment_edges
              (investment_id, investor_id, startup_id, round_name, round_stage,
               announced_date, amount, currency, is_lead, confidence_score, source_id, notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (edge_id, inv_id, sta_id, rel, None, None, None, None, None, conf, src_url, notes))
        created += 1

    conn.commit()
    conn.close()
    print(f"  Creadas: {created} | Ya existían: {skipped} | Errores: {errors}")

    if created == 0:
        print("  Nada nuevo — build-atlas omitido.")
        return

    # Step 3: build atlas
    print("\n  ── Step 3: build-atlas ─────────────────────────────────────")
    from src.capital_atlas import run as run_atlas
    atlas_stats = run_atlas(DB_PATH)
    print(f"  {atlas_stats}")
    print()


def cmd_fund_sweep_status(args: argparse.Namespace) -> None:
    from scripts.capital_sweep_status import run as run_status
    run_status(DB_PATH)


# ──────────────────────────────────────────────
# ingest-orgs
# ──────────────────────────────────────────────

def cmd_fund_gap_report(args: argparse.Namespace) -> None:
    from scripts.fund_gap_report import run as run_gap
    min_p = getattr(args, "min_portfolio", 1)
    top   = getattr(args, "top_funds", 20)
    inv   = getattr(args, "investor", None)
    print(f"\n  Fund Gap Report (min_portfolio={min_p}, top_funds={top})...\n")
    res = run_gap(DB_PATH, min_portfolio=min_p, top_funds=top, investor_filter=inv)
    print(f"  Inversores: {res['investors_analyzed']} | Candidatos: {res['total_candidates']}")
    print(f"\n  Top oportunidades:")
    for inv_id, cnt in res["top_opportunity_funds"]:
        print(f"    {inv_id:<35} {cnt:>3} sin edge")
    print(f"\n  Salida: quality/fund_gap_candidates.csv\n")


def cmd_build_ecosystem_graph(args: argparse.Namespace) -> None:
    from src.ecosystem_graph import run as run_eco
    print("\n  Building Ecosystem Graph data...\n")
    stats = run_eco(DB_PATH)
    print(f"\n  Summary: {stats}\n")


def cmd_ingest_orgs(args: argparse.Namespace) -> None:
    from src.ingest_orgs import ingest_all
    print("\n  Ingesting ecosystem organizations (gremiales / ESOs / corporates)...\n")
    stats = ingest_all(DB_PATH)
    total_inserted = sum(s.get("inserted", 0) for s in stats.values())
    total_errors   = sum(s.get("errors", 0) for s in stats.values())
    print(f"\n  Total insertado: {total_inserted} | Errores: {total_errors}\n")


def cmd_calibrate_scores(args: argparse.Namespace) -> None:
    import json
    from src.intelligence import _calibration_audit
    from pathlib import Path
    print("\n  Calibracion del scoring — auditoria de precision...\n")
    report = _calibration_audit(DB_PATH)
    if "error" in report:
        print(f"  [ERROR] {report['error']}\n")
        return
    print(f"  Inversores evaluados       : {report['investors_evaluated']}")
    print(f"  Startups de portfolio scored: {report['portfolio_startups_scored']}")
    print(f"  Precision@3                : {report['precision@3']:.1%}")
    print(f"  Precision@5                : {report['precision@5']:.1%}")
    print(f"  Precision@10               : {report['precision@10']:.1%}")
    print(f"  Mean rank portfolio startup: {report['mean_rank']:.1f}")
    print(f"\n  Peores inversores (menor precision@5):")
    for inv in report["worst_investors"]:
        print(f"    {inv['investor_name']:<35} P@5={inv['precision@5']:.2f}  mean_rank={inv['mean_rank']}")
    out = Path("quality") / "score_calibration.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  Salida: quality/score_calibration.json\n")


def cmd_embed_entities(args: argparse.Namespace) -> None:
    from src.embed_entities import run as run_embed_entities
    print("\n  Generando embeddings para entidades (orgs, ESOs, corporates)...\n")
    run_embed_entities()


def cmd_intelligence_data(args: argparse.Namespace) -> None:
    from src.intelligence import build_intelligence_data
    print("\n  Generando pilot/intelligence-data.js...\n")
    res = build_intelligence_data(DB_PATH)
    print(f"  Startups      : {res['startups']}")
    print(f"  Inversores    : {res['investors']}")
    print(f"  Todas ent.    : {res['entities']}")
    print(f"  Vectores      : {res['vec_shape']}")
    print(f"  Tiempo        : {res['elapsed']}s")
    print(f"\n  Salida: pilot/intelligence-data.js\n")


def cmd_ecosystem_health_data(args: argparse.Namespace) -> None:
    from src.intelligence import build_ecosystem_health_data
    print("\n  Generando pilot/ecosystem-health-data.js...\n")
    res = build_ecosystem_health_data(DB_PATH)
    print(f"  Startups      : {res['startups']}")
    print(f"  Financiadas   : {res['funded']}")
    print(f"  Celdas heatmap: {res['whitespace_cells']}")
    print(f"  Sin capital   : {res['isolated']}")
    print(f"  Momentum rows : {res['momentum_rows']}")
    print(f"  Tiempo        : {res['elapsed']}s")
    print(f"\n  Salida: pilot/ecosystem-health-data.js\n")


def cmd_taxonomy_cards(args: argparse.Namespace) -> None:
    from src.taxonomy_cards import run as run_cards
    print("\n  Frente B — Generando fichas de taxonomía...\n")
    res = run_cards(DB_PATH)
    print(f"  Temas         : {res['themes']}")
    print(f"  Startups      : {res['total_startups']}")
    print(f"\n  Salida: {res['output']}\n")


def cmd_orphan_triage(args: argparse.Namespace) -> None:
    from src.orphan_triage import run as run_orphan
    print("\n  Frente B — Triage de entidades startup huérfanas...\n")
    res = run_orphan(DB_PATH)
    print(f"  Huérfanas totales     : {res['total_orphans']}")
    for disp, n in sorted(res["by_disposition"].items()):
        print(f"    {disp:<22}: {n}")
    if res["probable_duplicates"]:
        print("\n  Duplicados probables (verificar + mergear):")
        for t in res["probable_duplicates"]:
            print(f"    {t['entity_id']:<28} → {t['duplicate_of']}")
    print("\n  Salida: quality/orphan_entities_triage.csv\n")


def cmd_reconcile_themes(args: argparse.Namespace) -> None:
    from src.reconcile_themes import run as run_reconcile
    dry = getattr(args, "dry_run", False)
    print(f"\n  Frente B — Reconciliar conflictos bio_theme ↔ cluster_label{' (dry-run)' if dry else ''}...\n")
    res = run_reconcile(DB_PATH, dry_run=dry)
    print(f"  Conflictos totales    : {res['total_conflicts']}")
    for verdict, n in sorted(res["by_verdict"].items()):
        print(f"    {verdict:<22}: {n}")
    print(f"  sub_cluster_label set : {res['sub_labels_updated']}")
    print(f"  Requieren revisión    : {res['isolated_review']} (isolated_review)")
    print("\n  Salida: quality/theme_cluster_mismatch_triage.csv\n")


def cmd_coverage(args: argparse.Namespace) -> None:
    from src.coverage import run as run_coverage
    print("\n  Frente A — Mapa de cobertura (parches, matriz tema×país, cola de des-sesgo)...\n")
    res = run_coverage(DB_PATH)
    print(f"  Parches en ledger : {res['ledger_patches']}")
    print(f"  Celdas tema×país  : {res['cells']}")
    for label, n in sorted(res["label_counts"].items()):
        print(f"    {label:<16}: {n}")
    print(f"  Tiers por país    :")
    for cc, tier in res["country_tiers"].items():
        print(f"    {cc:<4} {tier}")
    print(f"  Cola de des-sesgo : {res['debias_queue']} targets")
    print(f"  Tiempo            : {res['elapsed']}s")
    print("\n  Salidas: quality/coverage_ledger.csv, quality/coverage_matrix.csv,")
    print("           quality/coverage_debias_queue.csv, pilot/coverage-data.js\n")


def cmd_health(args: argparse.Namespace) -> None:
    from src.health import run as run_health
    run_health(DB_PATH)


def cmd_query(args: argparse.Namespace) -> None:
    from src.intelligence import semantic_search, _print_search_results
    query = " ".join(args.query)
    top_k = getattr(args, "top_k", 10)
    as_json = getattr(args, "json", False)
    filters: dict = {}
    if getattr(args, "theme", None): filters["theme"] = args.theme
    if getattr(args, "country", None): filters["country"] = args.country
    if getattr(args, "stage", None): filters["stage"] = args.stage

    results = semantic_search(query, top_k=top_k, filters=filters or None,
                               db_path=DB_PATH, as_json=as_json)
    if not as_json:
        _print_search_results(results, query)


def cmd_latent(args: argparse.Namespace) -> None:
    from src.intelligence import latent_potential, _print_latent
    entity_id = args.entity_id
    top_k = getattr(args, "top_k", 15)
    as_json = getattr(args, "json", False)

    result = latent_potential(entity_id, top_k=top_k, db_path=DB_PATH,
                               as_json=as_json)
    if not as_json:
        _print_latent(result)


def cmd_intro(args: argparse.Namespace) -> None:
    import json as _json
    from src.intro_builder import build_introduction_brief, print_brief
    entity_a = args.entity_a
    entity_b = args.entity_b
    as_json = getattr(args, "json", False)
    no_cab = getattr(args, "no_cab", False)
    brief = build_introduction_brief(
        entity_a, entity_b,
        db_path=DB_PATH,
        cab_context=not no_cab,
    )
    if as_json:
        print(_json.dumps(brief, ensure_ascii=False))
    else:
        print_brief(brief)


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
    ii = sub.add_parser("ingest-intake", help="staging/capital_intake.csv → canonical → build-atlas (ciclo completo en un paso)")
    ii.add_argument("--file", type=str, default=None, help="CSV de intake custom (default: staging/capital_intake.csv)")
    ii.add_argument("--dry-run", action="store_true", help="Solo muestra qué se ingresaría, sin escribir")
    sub.add_parser("fund-sweep-status", help="Dashboard de cobertura del grafo de capital + guía para el sweep")
    sub.add_parser("ingest-orgs", help="canonical/manual_canonical_organizations.csv + support/validation edges → ecosystem entities")
    sub.add_parser("build-ecosystem-graph", help="Regenerar pilot/ecosystem-graph-data.js desde SQLite (todas las capas)")
    fgr = sub.add_parser("fund-gap-report", help="Generar quality/fund_gap_candidates.csv — startups potenciales no mapeadas por inversor")
    fgr.add_argument("--min-portfolio", type=int, default=1, help="Solo fondos con >= N edges existentes")
    fgr.add_argument("--top-funds",     type=int, default=20, help="Analizar top N fondos (default: 20)")
    fgr.add_argument("--investor",      type=str, default=None, help="Filtrar a un inversor específico")
    sub.add_parser("quality-report", help="Genera pilot/quality-tracker.html con métricas de calidad")
    sub.add_parser("calibrate-scores", help="Audita precision@k del scoring de latent_potential() → quality/score_calibration.json")
    sub.add_parser("embed-entities", help="Genera embeddings para orgs/ESOs/corporates → embeddings/entity_vectors.npy")
    sub.add_parser("intelligence-data", help="Genera pilot/intelligence-data.js (vectores + metadatos + centroides)")
    sub.add_parser("ecosystem-health-data", help="Genera pilot/ecosystem-health-data.js (heatmap temas × países, isolated, momentum)")
    rt = sub.add_parser("reconcile-themes", help="Frente B: tipifica conflictos bio_theme↔cluster_label, alinea sub_cluster_label, emite triage CSV")
    rt.add_argument("--dry-run", action="store_true", help="Genera triage sin tocar DB")
    sub.add_parser("orphan-triage", help="Frente B: tipifica las entidades startup huérfanas (duplicado/fuera-scope/sin-procesar) → quality/orphan_entities_triage.csv")
    sub.add_parser("taxonomy-cards", help="Frente B: genera quality/taxonomy_cards.md (8 fichas: definición, fronteras, arquetipos, fuera-de-scope)")
    sub.add_parser("coverage", help="Mapa de cobertura: ledger de parches, matriz tema×país (bien_mapeado/parcial/no_explorado), cola de des-sesgo")
    sub.add_parser("health", help="Semáforo de salud del sistema en una pantalla (volumen, evidencia, consistencia, frescura, cobertura)")
    iq = sub.add_parser("query", help="Busqueda semantica de startups (texto libre)")
    iq.add_argument("query", nargs="+", help="Texto de busqueda")
    iq.add_argument("--top-k", type=int, default=10)
    iq.add_argument("--theme", type=str, default=None)
    iq.add_argument("--country", type=str, default=None)
    iq.add_argument("--stage", type=str, default=None)
    iq.add_argument("--json", action="store_true", help="Salida JSON (para server.js)")
    lp = sub.add_parser("latent", help="Potencial latente de una entidad (startup o inversor)")
    lp.add_argument("entity_id", help="ID de la entidad (startup_id o investor_id)")
    lp.add_argument("--top-k", type=int, default=15)
    lp.add_argument("--json", action="store_true", help="Salida JSON (para server.js)")
    ip = sub.add_parser("intro", help="Generar brief de introduccion entre dos entidades")
    ip.add_argument("entity_a", help="ID de la primera entidad")
    ip.add_argument("entity_b", help="ID de la segunda entidad")
    ip.add_argument("--no-cab", action="store_true", help="Omitir framing desde la CAB")
    ip.add_argument("--json", action="store_true", help="Salida JSON (para server.js)")

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
        "ingest-intake": cmd_ingest_intake,
        "fund-sweep-status": cmd_fund_sweep_status,
        "ingest-orgs": cmd_ingest_orgs,
        "build-ecosystem-graph": cmd_build_ecosystem_graph,
        "fund-gap-report": cmd_fund_gap_report,
        "quality-report": cmd_quality_report,
        "calibrate-scores": cmd_calibrate_scores,
        "embed-entities": cmd_embed_entities,
        "intelligence-data": cmd_intelligence_data,
        "ecosystem-health-data": cmd_ecosystem_health_data,
        "reconcile-themes": cmd_reconcile_themes,
        "orphan-triage": cmd_orphan_triage,
        "taxonomy-cards": cmd_taxonomy_cards,
        "coverage": cmd_coverage,
        "health": cmd_health,
        "query": cmd_query,
        "latent": cmd_latent,
        "intro": cmd_intro,
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
