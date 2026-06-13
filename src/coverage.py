"""
src/coverage.py — Frente A: honestidad de cobertura.

El mapa creció por parches de recolección (sweep de GridX, batches por país,
oleadas de web research). Este módulo hace visible ese sesgo:

1. coverage_ledger    — registro de parches históricos, reconstruido desde
                        audit_log + provenance fields (funding_source, scope_basis).
2. coverage_matrix    — score de cobertura por celda tema × país con etiqueta
                        honesta: bien_mapeado / parcial / no_explorado /
                        vacio_observado (cero startups en zona bien barrida —
                        eso sí es señal de whitespace real).
3. debias_queue       — cola priorizada de curación dirigida a las celdas y
                        fuentes más sesgadas, generada desde los datos.
4. pilot/coverage-data.js — bundle para que los dashboards declaren cobertura.

Principio: un observatorio que no distingue "no hay" de "no miramos" pierde
credibilidad. La ausencia solo se lee como inexistencia donde el barrido fue
suficiente.
"""
from __future__ import annotations

import pathlib
import sqlite3
import time
from datetime import datetime, timezone

from src.utils import clean, write_csv, write_js_global

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Países LATAM que el observatorio aspira a cubrir aunque hoy tengan 0 filas.
# Mantener celdas vacías visibles es el punto: el mapa debe mostrar dónde no miramos.
LATAM_TARGET_COUNTRIES = [
    "AR", "BR", "CL", "MX", "CO", "UY", "PE", "EC", "PY", "BO", "CR", "GT", "PA", "VE", "DO",
]

# Umbrales de exploración por país (documentados, ajustables).
# n_includes y diversidad de parches de provenance son los dos ejes:
# muchos startups vía UNA sola fuente sigue siendo un parche, no un barrido.
TIER_WELL_MIN_INCLUDES = 80
TIER_WELL_MIN_PATCHES = 3
TIER_PARTIAL_MIN_INCLUDES = 15
TIER_PARTIAL_MIN_PATCHES = 2

# Umbral de evidencia externa para que una celda se considere bien mapeada.
CELL_EVIDENCE_PCT = 0.60
# Si un solo parche aporta más de este % de una celda, la celda está sesgada
# a esa fuente aunque tenga volumen.
CELL_DOMINANT_SOURCE_PCT = 0.85


# ─────────────────────────────────────────────────────────────────────────────
# 1. Coverage ledger — parches históricos de recolección
# ─────────────────────────────────────────────────────────────────────────────

def build_ledger(conn: sqlite3.Connection) -> list[dict]:
    """Reconstruye los parches de recolección desde audit_log + provenance.

    Un "parche" = (mes, actor) en audit_log, enriquecido con qué países y
    tablas tocó. Se agregan además los parches de origen visibles en
    startup_extended.funding_source (p.ej. el import masivo de GridX), que
    son anteriores al audit_log o vinieron por CSV.
    """
    rows: list[dict] = []

    # Parches visibles en audit_log: (mes, actor) con alcance por país.
    audit_patches = conn.execute(
        """
        SELECT substr(a.timestamp, 1, 7) AS period,
               a.actor,
               count(*) AS n_changes,
               count(DISTINCT a.entity_id) AS n_entities,
               count(DISTINCT a.table_name) AS n_tables,
               group_concat(DISTINCT e.country_code) AS countries
        FROM audit_log a
        LEFT JOIN entities e ON e.entity_id = a.entity_id
        GROUP BY 1, 2
        ORDER BY 1, 3 DESC
        """
    ).fetchall()
    for period, actor, n_changes, n_entities, n_tables, countries in audit_patches:
        rows.append({
            "patch_id": f"audit:{period}:{actor}",
            "period": period,
            "method": actor or "unknown",
            "source_kind": "audit_log",
            "n_changes": n_changes,
            "n_entities": n_entities or 0,
            "countries_touched": _dedupe_codes(countries),
            "note": f"{n_tables} tabla(s) tocadas",
        })

    # Parches de provenance: funding_source agrupa el origen de cada startup.
    # gridx=230 includes es el parche fundacional y NO está en audit_log.
    prov_patches = conn.execute(
        """
        SELECT coalesce(nullif(sx.funding_source, ''), '(sin provenance)') AS src,
               count(*) AS n,
               group_concat(DISTINCT e.country_code) AS countries
        FROM startup_extended sx
        JOIN entities e ON e.entity_id = sx.startup_id
        WHERE sx.scope_decision = 'include'
        GROUP BY 1
        ORDER BY 2 DESC
        """
    ).fetchall()
    for src, n, countries in prov_patches:
        rows.append({
            "patch_id": f"provenance:{src}",
            "period": "(histórico)",
            "method": src,
            "source_kind": "funding_source",
            "n_changes": "",
            "n_entities": n,
            "countries_touched": _dedupe_codes(countries),
            "note": "origen declarado en startup_extended.funding_source (includes)",
        })

    return rows


def _dedupe_codes(concat: str | None) -> str:
    if not concat:
        return ""
    seen: list[str] = []
    for code in concat.split(","):
        code = code.strip()
        if code and code not in seen:
            seen.append(code)
    return ";".join(sorted(seen))


# ─────────────────────────────────────────────────────────────────────────────
# 2. Matriz de cobertura tema × país
# ─────────────────────────────────────────────────────────────────────────────

def _country_stats(conn: sqlite3.Connection) -> dict[str, dict]:
    """Stats de exploración por país sobre el universo include."""
    stats: dict[str, dict] = {}
    rows = conn.execute(
        """
        SELECT coalesce(e.country_code, '??') AS cc,
               count(*) AS n_inc,
               sum(CASE WHEN sx.scope_basis = 'external_auditable_source' THEN 1 ELSE 0 END) AS n_evid,
               count(DISTINCT nullif(sx.funding_source, '')) AS n_patches,
               sum(CASE WHEN EXISTS (
                   SELECT 1 FROM investment_edges ie WHERE ie.startup_id = sx.startup_id
               ) THEN 1 ELSE 0 END) AS n_with_capital
        FROM startup_extended sx
        JOIN entities e ON e.entity_id = sx.startup_id
        WHERE sx.scope_decision = 'include'
        GROUP BY 1
        """
    ).fetchall()
    for cc, n_inc, n_evid, n_patches, n_capital in rows:
        stats[cc] = {
            "n_includes": n_inc,
            "evidence_pct": round(n_evid / n_inc, 3) if n_inc else 0.0,
            "n_patches": n_patches,
            "capital_pct": round(n_capital / n_inc, 3) if n_inc else 0.0,
        }

    # Inversores locales con al menos una arista: proxy de qué tan barrida
    # está la red de capital de ese país (no solo sus startups).
    inv_rows = conn.execute(
        """
        SELECT coalesce(e.country_code, '??') AS cc, count(DISTINCT i.investor_id)
        FROM investors i
        JOIN entities e ON e.entity_id = i.investor_id
        WHERE EXISTS (SELECT 1 FROM investment_edges ie WHERE ie.investor_id = i.investor_id)
        GROUP BY 1
        """
    ).fetchall()
    for cc, n_inv in inv_rows:
        stats.setdefault(cc, {"n_includes": 0, "evidence_pct": 0.0, "n_patches": 0, "capital_pct": 0.0})
        stats[cc]["n_local_investors"] = n_inv

    for cc in LATAM_TARGET_COUNTRIES:
        stats.setdefault(cc, {"n_includes": 0, "evidence_pct": 0.0, "n_patches": 0, "capital_pct": 0.0})

    for cc, s in stats.items():
        s.setdefault("n_local_investors", 0)
        s["tier"] = _exploration_tier(cc, s)
    return stats


def _exploration_tier(cc: str, s: dict) -> str:
    # El observatorio mapea LATAM. Startups con sede fuera (US, NL, etc.)
    # entran por su operación en la región, pero esos países no son objetivo
    # de barrido: su baja cobertura no es deuda, es foco.
    if cc not in LATAM_TARGET_COUNTRIES:
        return "fuera_de_foco"
    if s["n_includes"] >= TIER_WELL_MIN_INCLUDES and s["n_patches"] >= TIER_WELL_MIN_PATCHES:
        return "well_mapped"
    if s["n_includes"] >= TIER_PARTIAL_MIN_INCLUDES and s["n_patches"] >= TIER_PARTIAL_MIN_PATCHES:
        return "partial"
    return "under_explored"


def build_matrix(conn: sqlite3.Connection, country_stats: dict[str, dict]) -> list[dict]:
    """Celdas tema × país con etiqueta de cobertura honesta."""
    themes = [r[0] for r in conn.execute(
        "SELECT DISTINCT bio_theme_primary FROM startup_extended "
        "WHERE scope_decision='include' AND bio_theme_primary IS NOT NULL "
        "ORDER BY 1"
    ).fetchall()]

    cell_rows = conn.execute(
        """
        SELECT sx.bio_theme_primary AS theme,
               coalesce(e.country_code, '??') AS cc,
               count(*) AS n,
               sum(CASE WHEN sx.scope_basis = 'external_auditable_source' THEN 1 ELSE 0 END) AS n_evid,
               sum(CASE WHEN EXISTS (
                   SELECT 1 FROM investment_edges ie WHERE ie.startup_id = sx.startup_id
               ) THEN 1 ELSE 0 END) AS n_capital
        FROM startup_extended sx
        JOIN entities e ON e.entity_id = sx.startup_id
        WHERE sx.scope_decision = 'include' AND sx.bio_theme_primary IS NOT NULL
        GROUP BY 1, 2
        """
    ).fetchall()
    cells = {(t, cc): (n, ne, nc) for t, cc, n, ne, nc in cell_rows}

    # Fuente dominante por celda (¿la celda existe solo gracias a un parche?)
    dom_rows = conn.execute(
        """
        SELECT theme, cc, src, n FROM (
            SELECT sx.bio_theme_primary AS theme,
                   coalesce(e.country_code, '??') AS cc,
                   coalesce(nullif(sx.funding_source, ''), '(sin provenance)') AS src,
                   count(*) AS n,
                   row_number() OVER (
                       PARTITION BY sx.bio_theme_primary, e.country_code
                       ORDER BY count(*) DESC
                   ) AS rk
            FROM startup_extended sx
            JOIN entities e ON e.entity_id = sx.startup_id
            WHERE sx.scope_decision = 'include' AND sx.bio_theme_primary IS NOT NULL
            GROUP BY 1, 2, 3
        ) WHERE rk = 1
        """
    ).fetchall()
    dominant = {(t, cc): (src, n) for t, cc, src, n in dom_rows}

    countries = sorted(set(LATAM_TARGET_COUNTRIES) | {
        cc for (_, cc) in cells if cc and cc != "??"
    })

    out: list[dict] = []
    for theme in themes:
        for cc in countries:
            n, n_evid, n_capital = cells.get((theme, cc), (0, 0, 0))
            cstats = country_stats.get(cc, {})
            tier = cstats.get("tier", "under_explored")
            dom_src, dom_n = dominant.get((theme, cc), ("", 0))
            dom_share = round(dom_n / n, 3) if n else 0.0
            evid_pct = round(n_evid / n, 3) if n else 0.0
            label = _cell_label(tier, n, evid_pct, dom_share)
            out.append({
                "theme": theme,
                "country": cc,
                "n_startups": n,
                "evidence_pct": evid_pct,
                "capital_pct": round(n_capital / n, 3) if n else 0.0,
                "dominant_source": dom_src,
                "dominant_source_share": dom_share,
                "country_tier": tier,
                "coverage_label": label,
            })
    return out


def _cell_label(tier: str, n: int, evid_pct: float, dom_share: float) -> str:
    """Etiqueta honesta de la celda.

    - fuera_de_foco:   país no-LATAM — no es objetivo de barrido.
    - no_explorado:    el país está poco barrido — la ausencia NO es dato.
    - vacio_observado: cero startups en un país bien/parcialmente barrido —
                       esto SÍ es señal de whitespace real.
    - bien_mapeado:    volumen + evidencia externa + sin dependencia extrema
                       de un solo parche.
    - parcial:         hay datos pero con evidencia floja o mono-fuente.
    """
    if tier == "fuera_de_foco":
        return "fuera_de_foco"
    if tier == "under_explored":
        return "no_explorado"
    if n == 0:
        return "vacio_observado"
    if tier == "well_mapped" and evid_pct >= CELL_EVIDENCE_PCT and dom_share <= CELL_DOMINANT_SOURCE_PCT:
        return "bien_mapeado"
    return "parcial"


# ─────────────────────────────────────────────────────────────────────────────
# 3. Cola de des-sesgo
# ─────────────────────────────────────────────────────────────────────────────

def build_debias_queue(
    conn: sqlite3.Connection,
    country_stats: dict[str, dict],
    matrix: list[dict],
) -> list[dict]:
    """Cola de curación dirigida, generada desde los datos (no desde intuición).

    Tres familias de targets:
    a) países under_explored → barrido dirigido (con inversores locales ya en
       DB como punto de entrada concreto).
    b) inversores con portfolio aparentemente sub-barrido (pocas aristas en un
       país parcial/under) → completar sweep de ese portfolio.
    c) celdas parciales donde un solo parche domina → diversificar fuentes.
    """
    queue: list[dict] = []

    # (a) países poco explorados, ordenados por lo que ya sabemos que tienen
    for cc, s in sorted(country_stats.items(), key=lambda kv: -kv[1]["n_includes"]):
        if cc in ("??",) or cc not in LATAM_TARGET_COUNTRIES:
            continue
        if s["tier"] != "under_explored":
            continue
        invs = conn.execute(
            """
            SELECT i.investor_id, count(ie.investment_id) AS n
            FROM investors i
            JOIN entities e ON e.entity_id = i.investor_id
            LEFT JOIN investment_edges ie ON ie.investor_id = i.investor_id
            WHERE e.country_code = ?
            GROUP BY 1 ORDER BY 2 DESC LIMIT 5
            """,
            (cc,),
        ).fetchall()
        entry_points = "; ".join(f"{iid} ({n} edges)" for iid, n in invs) or "(sin inversores locales en DB)"
        queue.append({
            "priority": "alta",
            "kind": "country_sweep",
            "target": cc,
            "evidence": f"{s['n_includes']} includes, {s['n_patches']} parches, {s.get('n_local_investors', 0)} inversores locales con edges",
            "action": f"Barrido dirigido de portfolios y aceleradoras bio de {cc}. Puntos de entrada ya en DB: {entry_points}",
        })

    # (b) inversores sub-barridos en países no bien mapeados
    inv_rows = conn.execute(
        """
        SELECT i.investor_id, coalesce(e.country_code, '??') AS cc,
               count(ie.investment_id) AS n_edges
        FROM investors i
        JOIN entities e ON e.entity_id = i.investor_id
        LEFT JOIN investment_edges ie ON ie.investor_id = i.investor_id
        GROUP BY 1, 2
        HAVING n_edges BETWEEN 1 AND 4
        ORDER BY cc, n_edges
        """
    ).fetchall()
    for investor_id, cc, n_edges in inv_rows:
        tier = country_stats.get(cc, {}).get("tier", "under_explored")
        queue.append({
            "priority": "media",
            "kind": "portfolio_sweep",
            "target": investor_id,
            "evidence": f"solo {n_edges} edge(s) en DB; país {cc} ({tier})",
            "action": f"Revisar portfolio público completo de {investor_id} y mapear startups bio faltantes",
        })

    # (c) celdas con volumen pero mono-fuente
    for cell in matrix:
        if cell["coverage_label"] != "parcial":
            continue
        if cell["n_startups"] >= 5 and cell["dominant_source_share"] > CELL_DOMINANT_SOURCE_PCT:
            queue.append({
                "priority": "media",
                "kind": "diversify_sources",
                "target": f"{cell['theme']} × {cell['country']}",
                "evidence": (
                    f"{cell['n_startups']} startups, {int(cell['dominant_source_share']*100)}% "
                    f"viene de '{cell['dominant_source']}'"
                ),
                "action": "Buscar la celda vía fuentes independientes del parche dominante (medios, otras carteras, registros)",
            })

    # (d) celdas vacías observadas en países bien mapeados = whitespace real,
    # pero verificar antes de afirmarlo en producto.
    for cell in matrix:
        if cell["coverage_label"] == "vacio_observado" and cell["country_tier"] == "well_mapped":
            queue.append({
                "priority": "baja",
                "kind": "confirm_whitespace",
                "target": f"{cell['theme']} × {cell['country']}",
                "evidence": "0 startups en país bien barrido",
                "action": "Verificación rápida antes de declararlo whitespace real en producto",
            })

    return queue


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def run(db_path: pathlib.Path) -> dict:
    t0 = time.time()
    conn = sqlite3.connect(db_path)

    ledger = build_ledger(conn)
    country_stats = _country_stats(conn)
    matrix = build_matrix(conn, country_stats)
    queue = build_debias_queue(conn, country_stats, matrix)

    write_csv(ROOT / "quality" / "coverage_ledger.csv", ledger,
              ["patch_id", "period", "method", "source_kind", "n_changes",
               "n_entities", "countries_touched", "note"])
    write_csv(ROOT / "quality" / "coverage_matrix.csv", matrix,
              ["theme", "country", "n_startups", "evidence_pct", "capital_pct",
               "dominant_source", "dominant_source_share", "country_tier",
               "coverage_label"])
    write_csv(ROOT / "quality" / "coverage_debias_queue.csv", queue,
              ["priority", "kind", "target", "evidence", "action"])

    label_counts: dict[str, int] = {}
    for cell in matrix:
        label_counts[cell["coverage_label"]] = label_counts.get(cell["coverage_label"], 0) + 1

    countries_payload = {
        cc: {
            "tier": s["tier"],
            "n_includes": s["n_includes"],
            "evidence_pct": s["evidence_pct"],
            "n_patches": s["n_patches"],
            "n_local_investors": s.get("n_local_investors", 0),
        }
        for cc, s in country_stats.items()
    }
    write_js_global(ROOT / "pilot" / "coverage-data.js", "COVERAGE_DATA", {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "countries": countries_payload,
        "cells": matrix,
        "label_counts": label_counts,
        "debias_queue_size": len(queue),
        "legend": {
            "bien_mapeado": "Volumen + evidencia externa + fuentes diversas: la celda es confiable.",
            "parcial": "Hay datos, pero con evidencia floja o dependientes de un solo parche.",
            "no_explorado": "País poco barrido: la ausencia NO significa inexistencia.",
            "fuera_de_foco": "País no-LATAM: presente por operación regional, no es objetivo de barrido.",
            "vacio_observado": "Cero startups en zona bien barrida: candidato a whitespace real.",
        },
    })

    conn.close()
    return {
        "ledger_patches": len(ledger),
        "cells": len(matrix),
        "label_counts": label_counts,
        "country_tiers": {cc: s["tier"] for cc, s in sorted(country_stats.items())},
        "debias_queue": len(queue),
        "elapsed": round(time.time() - t0, 1),
    }
