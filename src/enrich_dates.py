"""
src/enrich_dates.py — Enriquecimiento de fechas en investment_edges.

Estrategia honesta de dos pasos:
1. PROPAGACIÓN AUTOMÁTICA (alta confianza): si un co-inversor en la MISMA ronda
   (mismo startup + mismo round_stage) tiene announced_date conocida, todos los
   co-inversores sin fecha en esa ronda reciben la misma fecha.
   Justificación: una ronda tiene UNA fecha de anuncio; múltiples inversores
   participan en el mismo evento.

2. COLA DE CURATION: ranking priorizado de edges sin fecha para investigación
   manual, ordenadas por impacto potencial.

Salidas:
  quality/date_enrichment_queue.csv  — cola de curation priorizada
  quality/date_propagation_log.md    — log de las propagaciones automáticas

Uso:
    python pipeline.py enrich-dates            # propaga + genera cola
    python pipeline.py enrich-dates --dry-run  # solo muestra qué haría
"""
from __future__ import annotations

import pathlib
import sqlite3
from collections import defaultdict
from datetime import date

from src.audit import diff_and_log_update

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _propagate_coround_dates(conn: sqlite3.Connection, dry_run: bool = False) -> list[dict]:
    """
    Propaga fechas de co-inversores en el mismo round.
    Mismo startup + mismo round_stage con fecha conocida → mismo announced_date.
    """
    rows = conn.execute("""
        SELECT DISTINCT
            ie_nd.investment_id,
            ie_nd.investor_id,
            ie_nd.startup_id,
            ie_nd.round_stage,
            ie_d.announced_date AS propagate_date,
            ie_d.investor_id    AS source_investor
        FROM investment_edges ie_nd
        JOIN investment_edges ie_d
            ON  ie_d.startup_id   = ie_nd.startup_id
            AND ie_d.round_stage  = ie_nd.round_stage
            AND ie_d.announced_date IS NOT NULL
            AND ie_d.announced_date != ''
            AND ie_d.investor_id  != ie_nd.investor_id
        WHERE (ie_nd.announced_date IS NULL OR ie_nd.announced_date = '')
        GROUP BY ie_nd.investment_id
        ORDER BY ie_d.announced_date DESC
    """).fetchall()

    # De-duplicate: tomar la fecha más reciente cuando hay múltiples fuentes para el mismo edge
    seen: dict[str, dict] = {}
    for inv_id, investor, startup, stage, prop_date, src_inv in rows:
        if inv_id not in seen or prop_date > seen[inv_id]["propagate_date"]:
            seen[inv_id] = {
                "investment_id":   inv_id,
                "investor_id":     investor,
                "startup_id":      startup,
                "round_stage":     stage,
                "propagate_date":  prop_date,
                "source_investor": src_inv,
            }

    updates = list(seen.values())

    if not dry_run:
        for u in updates:
            diff_and_log_update(
                conn,
                table="investment_edges",
                row_id_col="investment_id",
                row_id=u["investment_id"],
                new_values={"announced_date": u["propagate_date"]},
                actor="enrich_dates",
                reason=f"co-round propagation: same startup+stage as {u['source_investor']}",
                evidence_url="",
            )
        conn.commit()

    return updates


def _build_curation_queue(conn: sqlite3.Connection) -> list[dict]:
    """
    Genera cola priorizada de edges sin fecha para investigación manual.
    Score = (startup_valuation_tier * 3) + (stage_rank * 2) + (has_amount) + (co_investors_have_dates * 2)
    """
    STAGE_RANK = {
        "ipo": 7, "exit": 7, "acquisition": 7,
        "growth": 6, "series-d": 6, "private-equity": 6,
        "series-c": 5, "series-b": 4, "pre-series-c": 4,
        "series-a": 3, "seed": 2, "pre-seed": 1, "accelerator": 0,
    }

    rows = conn.execute("""
        SELECT
            ie.investment_id,
            ie.investor_id,
            ie.startup_id,
            ie.round_stage,
            ie.amount,
            ie.source_id,
            COALESCE(sx.valuation_tier, 0)    AS vtier,
            COALESCE(sx.bio_theme_primary, '') AS theme,
            COALESCE(e.canonical_name, ie.startup_id) AS startup_name,
            e.country_code
        FROM investment_edges ie
        LEFT JOIN startup_extended sx ON sx.startup_id = ie.startup_id
        LEFT JOIN entities e ON e.entity_id = ie.startup_id
        WHERE (ie.announced_date IS NULL OR ie.announced_date = '')
        AND COALESCE(ie.source_id,'') NOT LIKE '%inferred%'
    """).fetchall()

    # Build set of startups that have at least one dated edge (to flag "resolvable via research")
    dated_startups = set(conn.execute("""
        SELECT DISTINCT startup_id FROM investment_edges
        WHERE announced_date IS NOT NULL AND announced_date != ''
    """).fetchall() or [])
    dated_startups = {r[0] for r in dated_startups}

    # Count co-investors with dates per (startup, stage)
    coround_dated = defaultdict(int)
    for row in conn.execute("""
        SELECT startup_id, round_stage, COUNT(*)
        FROM investment_edges
        WHERE announced_date IS NOT NULL AND announced_date != ''
        GROUP BY startup_id, round_stage
    """).fetchall():
        coround_dated[(row[0], row[1])] = row[2]

    queue = []
    for row in rows:
        inv_id, investor, startup, stage, amount, source, vtier, theme, sname, country = row
        stage_r = STAGE_RANK.get((stage or "").lower(), 0)
        has_amt = 1 if amount else 0
        co_dated = min(coround_dated.get((startup, stage), 0), 3)  # cap contribution at 3
        in_dated_startup = 1 if startup in dated_startups else 0

        vtier_int = int(float(vtier or 0))
        score = (vtier_int * 3) + (stage_r * 2) + has_amt + (co_dated * 2) + in_dated_startup

        queue.append({
            "priority_score":  score,
            "investment_id":   inv_id,
            "investor_id":     investor,
            "startup_id":      startup,
            "startup_name":    sname,
            "country":         country or "",
            "round_stage":     stage or "",
            "has_amount":      has_amt,
            "valuation_tier":  vtier_int,
            "bio_theme":       theme,
            "source_id":       (source or "")[:80],
            "research_hint":   _research_hint(investor, startup, stage),
        })

    queue.sort(key=lambda x: -x["priority_score"])
    return queue


def _research_hint(investor: str, startup: str, stage: str) -> str:
    """Sugiere dónde buscar la fecha para esta arista específica."""
    stage = (stage or "").lower()
    if stage in ("series-a", "series-b", "series-c", "series-d", "growth"):
        return f"Crunchbase: {startup} funding rounds | TechCrunch/Forbes/press release"
    if stage in ("seed", "pre-seed"):
        return f"Crunchbase: {startup} | fondo: {investor} newsletter/portfolio"
    if stage in ("accelerator",):
        return f"Sitio de {investor}: batch/cohort list con fechas"
    return f"Crunchbase: {startup} | LinkedIn announcement | {investor} portfolio"


def _write_queue(queue: list[dict], path: pathlib.Path) -> None:
    import csv
    fields = ["priority_score", "investment_id", "investor_id", "startup_name",
              "startup_id", "country", "round_stage", "bio_theme",
              "valuation_tier", "has_amount", "source_id", "research_hint"]
    path.parent.mkdir(exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(queue)


def _write_log(updates: list[dict], path: pathlib.Path) -> None:
    today = date.today().isoformat()
    lines = [
        f"# Date Propagation Log — {today}\n",
        f"Edges actualizadas por co-round propagation: **{len(updates)}**\n",
        "",
        "| investment_id | investor | startup | stage | fecha_propagada | fuente |\n",
        "|---|---|---|---|---|---|\n",
    ]
    for u in updates:
        lines.append(
            f"| {u['investment_id']} | {u['investor_id']} | {u['startup_id']} "
            f"| {u['round_stage']} | {u['propagate_date']} | via {u['source_investor']} |\n"
        )
    lines += [
        "",
        "## Metodología\n",
        "Co-round propagation: si un co-inversor en la MISMA ronda (mismo startup + "
        "mismo round_stage) tiene announced_date conocida, todos los participantes sin "
        "fecha en esa ronda reciben la misma fecha. Razonamiento: una ronda tiene una "
        "única fecha de anuncio público; los múltiples inversores participan en el "
        "mismo evento.\n",
    ]
    path.write_text("".join(lines), encoding="utf-8")


def run(db_path: pathlib.Path, dry_run: bool = False) -> dict:
    conn = sqlite3.connect(db_path)

    propagated = _propagate_coround_dates(conn, dry_run=dry_run)
    queue      = _build_curation_queue(conn)
    conn.close()

    queue_path = ROOT / "quality" / "date_enrichment_queue.csv"
    log_path   = ROOT / "quality" / "date_propagation_log.md"

    _write_queue(queue, queue_path)
    if not dry_run:
        _write_log(propagated, log_path)

    return {
        "propagated":   len(propagated),
        "queue_size":   len(queue),
        "queue_path":   str(queue_path),
        "dry_run":      dry_run,
    }
