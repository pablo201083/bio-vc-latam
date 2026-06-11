"""
src/capital_structure.py — Frente C: estructura de inversión real.

Convierte el grafo de capital (quién invirtió en quién) en estructura legible:
pirámide de stages por tema, cohortes, sindicación, dependencia de capital
extranjero y concentración. Usa el stage REAL de las aristas (round_stage), no
el funding_stage de startup_extended (que infla pre-seed como piso por default).

Honestidad de datos:
- El stage de una startup = el más avanzado entre sus aristas con round_stage.
- Las startups sin arista se reportan aparte como "capital no documentado",
  no se asumen pre-seed.
- Sin montos confiables (solo 10% de aristas), la pirámide cuenta EMPRESAS por
  stage, no capital movilizado. El embudo es de progresión, no de dólares.

Salidas:
  pilot/capital-structure-data.js   (window.CAPITAL_STRUCTURE)
  quality/capital_structure_report.md

Uso:
    python pipeline.py capital-structure
"""
from __future__ import annotations

import pathlib
import sqlite3
from collections import Counter, defaultdict
from datetime import date

from src.utils import write_js_global

ROOT = pathlib.Path(__file__).resolve().parent.parent

LATAM = {"AR", "BR", "CL", "MX", "CO", "UY", "PE", "EC", "PY", "BO", "CR", "GT", "PA", "VE", "DO"}

# Orden canónico de progresión y agrupación en niveles de pirámide.
STAGE_RANK = {
    "accelerator": 0, "pre-seed": 1, "seed": 2, "series-a": 3,
    "series-b": 4, "pre-series-c": 4, "series-c": 5, "series-d": 6,
    "growth": 6, "private-equity": 6, "pipe": 6, "strategic": 6,
    "ipo": 7, "exit": 7, "acquisition": 7,
}
PYRAMID_LEVELS = [
    ("Pre-seed / Accelerator", {"accelerator", "pre-seed"}),
    ("Seed", {"seed"}),
    ("Series A", {"series-a"}),
    ("Growth (B–D)", {"series-b", "pre-series-c", "series-c", "series-d", "growth", "private-equity", "pipe", "strategic"}),
    ("Exit / IPO", {"ipo", "exit", "acquisition"}),
]


def _stage_level(stage: str) -> str | None:
    for name, members in PYRAMID_LEVELS:
        if stage in members:
            return name
    return None


def _startup_top_stage(conn: sqlite3.Connection) -> dict[str, str]:
    """startup_id → stage más avanzado entre sus aristas con round_stage."""
    rows = conn.execute(
        "SELECT startup_id, round_stage FROM investment_edges "
        "WHERE round_stage IS NOT NULL AND round_stage <> '' AND round_stage <> 'undisclosed'"
    ).fetchall()
    best: dict[str, str] = {}
    for sid, stage in rows:
        if stage not in STAGE_RANK:
            continue
        if sid not in best or STAGE_RANK[stage] > STAGE_RANK[best[sid]]:
            best[sid] = stage
    return best


def _themes(conn: sqlite3.Connection) -> dict[str, str]:
    return dict(conn.execute(
        "SELECT startup_id, bio_theme_primary FROM startup_extended "
        "WHERE scope_decision='include' AND bio_theme_primary IS NOT NULL"
    ).fetchall())


def stage_pyramid(conn, theme_map, top_stage) -> dict:
    """Pirámide global y por tema. Detecta temas con base sin cúspide."""
    global_levels = Counter()
    by_theme: dict[str, Counter] = defaultdict(Counter)
    no_capital: Counter = Counter()

    for sid, theme in theme_map.items():
        stage = top_stage.get(sid)
        if stage is None:
            no_capital[theme] += 1
            continue
        lvl = _stage_level(stage)
        if lvl:
            global_levels[lvl] += 1
            by_theme[theme][lvl] += 1

    level_order = [n for n, _ in PYRAMID_LEVELS]
    themes_out = {}
    for theme, counts in by_theme.items():
        funded = sum(counts.values())
        growth_plus = counts["Series A"] + counts["Growth (B–D)"] + counts["Exit / IPO"]
        early = counts["Pre-seed / Accelerator"] + counts["Seed"]
        themes_out[theme] = {
            "levels": {lvl: counts.get(lvl, 0) for lvl in level_order},
            "funded": funded,
            "no_capital_documented": no_capital.get(theme, 0),
            "early_to_growth_ratio": round(growth_plus / early, 2) if early else None,
        }
    return {
        "global": {lvl: global_levels.get(lvl, 0) for lvl in level_order},
        "by_theme": themes_out,
        "level_order": level_order,
    }


def cohorts(conn, theme_map) -> dict:
    """Startups include por año de fundación + cuántas con capital."""
    rows = conn.execute(
        """
        SELECT e.founded_year,
               sum(CASE WHEN EXISTS(SELECT 1 FROM investment_edges ie WHERE ie.startup_id=sx.startup_id)
                        THEN 1 ELSE 0 END) AS funded,
               count(*) AS total
        FROM startup_extended sx JOIN entities e ON e.entity_id=sx.startup_id
        WHERE sx.scope_decision='include' AND e.founded_year IS NOT NULL
          AND e.founded_year > 1990
        GROUP BY 1 ORDER BY 1
        """
    ).fetchall()
    return {"by_year": [{"year": int(y), "funded": f, "total": t} for y, f, t in rows]}


def syndication(conn) -> dict:
    """Red de co-inversión: pares de fondos que invierten en las mismas startups."""
    pairs = conn.execute(
        """
        SELECT a.investor_id, b.investor_id, count(*) AS n
        FROM investment_edges a
        JOIN investment_edges b ON a.startup_id=b.startup_id AND a.investor_id < b.investor_id
        GROUP BY 1,2 HAVING n >= 2 ORDER BY n DESC
        """
    ).fetchall()
    edges = [{"source": a, "target": b, "weight": n} for a, b, n in pairs]
    degree = Counter()
    for a, b, n in pairs:
        degree[a] += 1
        degree[b] += 1
    return {
        "pairs": edges[:60],
        "total_pairs": len(edges),
        "most_syndicated": degree.most_common(12),
    }


def foreign_dependence(conn, theme_map) -> dict:
    """Por tema: % de aristas cuyo inversor es no-LATAM."""
    rows = conn.execute(
        """
        SELECT ie.startup_id, e.country_code
        FROM investment_edges ie JOIN entities e ON e.entity_id=ie.investor_id
        """
    ).fetchall()
    theme_total: Counter = Counter()
    theme_foreign: Counter = Counter()
    for sid, cc in rows:
        theme = theme_map.get(sid)
        if not theme:
            continue
        theme_total[theme] += 1
        if cc and cc not in LATAM:
            theme_foreign[theme] += 1
    out = {}
    for theme, total in theme_total.items():
        out[theme] = {
            "edges": total,
            "foreign_edges": theme_foreign.get(theme, 0),
            "foreign_pct": round(theme_foreign.get(theme, 0) / total, 3) if total else 0,
        }
    return out


def concentration(conn, theme_map) -> dict:
    """HHI de inversores por tema: 1.0 = un solo inversor; ~0 = muy distribuido."""
    theme_inv: dict[str, Counter] = defaultdict(Counter)
    rows = conn.execute("SELECT startup_id, investor_id FROM investment_edges").fetchall()
    for sid, inv in rows:
        theme = theme_map.get(sid)
        if theme:
            theme_inv[theme][inv] += 1
    out = {}
    for theme, counts in theme_inv.items():
        total = sum(counts.values())
        hhi = sum((n / total) ** 2 for n in counts.values()) if total else 0
        top_inv, top_n = counts.most_common(1)[0]
        out[theme] = {
            "hhi": round(hhi, 3),
            "n_investors": len(counts),
            "top_investor": top_inv,
            "top_investor_share": round(top_n / total, 3) if total else 0,
        }
    return out


def capital_gap(conn, theme_map, top_stage) -> dict:
    """Las startups include sin arista de capital documentada, por tema."""
    no_cap: Counter = Counter()
    total: Counter = Counter()
    for sid, theme in theme_map.items():
        total[theme] += 1
        has_edge = conn.execute(
            "SELECT 1 FROM investment_edges WHERE startup_id=? LIMIT 1", (sid,)
        ).fetchone()
        if not has_edge:
            no_cap[theme] += 1
    return {
        "total_without_capital": sum(no_cap.values()),
        "by_theme": {t: {"without_capital": no_cap.get(t, 0), "total": total[t],
                         "pct": round(no_cap.get(t, 0) / total[t], 3)}
                     for t in total},
    }


def _report(res: dict) -> str:
    L = ["# Estructura de Inversión — BIO VC LATAM\n",
         f"_Generado {date.today().isoformat()} con `python pipeline.py capital-structure`. "
         "Cuenta EMPRESAS por stage (no dólares: solo 10% de aristas tiene monto). "
         "El stage es el más avanzado entre las aristas reales con round_stage._\n"]

    p = res["pyramid"]
    L.append("## Pirámide de stages (global)\n")
    for lvl in p["level_order"]:
        n = p["global"][lvl]
        L.append(f"- **{lvl}**: {n} {'█' * min(n // 5, 40)}")
    L.append("")

    L.append("## Pirámide por tema — ¿base sin cúspide?\n")
    L.append("| Tema | Pre-seed | Seed | Ser.A | Growth | Exit | Sin capital | A→Growth |")
    L.append("|------|---------|------|-------|--------|------|-------------|----------|")
    for theme, d in sorted(p["by_theme"].items(), key=lambda kv: -kv[1]["funded"]):
        lv = d["levels"]
        L.append(f"| {theme} | {lv['Pre-seed / Accelerator']} | {lv['Seed']} | "
                 f"{lv['Series A']} | {lv['Growth (B–D)']} | {lv['Exit / IPO']} | "
                 f"{d['no_capital_documented']} | {d['early_to_growth_ratio'] if d['early_to_growth_ratio'] is not None else '—'} |")
    L.append("")

    fd = res["foreign_dependence"]
    L.append("## Dependencia de capital extranjero por tema\n")
    L.append("| Tema | Aristas | Extranjeras | % extranjero |")
    L.append("|------|---------|-------------|--------------|")
    for theme, d in sorted(fd.items(), key=lambda kv: -kv[1]["foreign_pct"]):
        L.append(f"| {theme} | {d['edges']} | {d['foreign_edges']} | {int(d['foreign_pct']*100)}% |")
    L.append("")

    co = res["concentration"]
    L.append("## Concentración de capital por tema (HHI)\n")
    L.append("> ⚠️ **Sesgo de recolección:** GridX aparece dominante en casi todos los temas "
             "porque su portfolio se barrió exhaustivamente (ver Frente A / `coverage`). La "
             "concentración real es menor; leer junto al mapa de cobertura, no como verdad de mercado.\n")
    L.append("| Tema | HHI | # inversores | Inversor dominante | Share |")
    L.append("|------|-----|--------------|--------------------|-------|")
    for theme, d in sorted(co.items(), key=lambda kv: -kv[1]["hhi"]):
        L.append(f"| {theme} | {d['hhi']} | {d['n_investors']} | {d['top_investor']} | {int(d['top_investor_share']*100)}% |")
    L.append("")

    sy = res["syndication"]
    L.append("## Sindicación (co-inversión)\n")
    L.append(f"{sy['total_pairs']} pares de fondos co-invierten en ≥2 startups. Más sindicados:\n")
    for inv, deg in sy["most_syndicated"]:
        L.append(f"- **{inv}**: co-invierte con {deg} fondos distintos")
    L.append("\nTop pares:\n")
    for e in sy["pairs"][:8]:
        L.append(f"- {e['source']} + {e['target']}: {e['weight']} startups en común")
    L.append("")

    g = res["capital_gap"]
    L.append(f"## Capital no documentado\n")
    L.append(f"{g['total_without_capital']} startups include sin ninguna arista de capital. Por tema:\n")
    for theme, d in sorted(g["by_theme"].items(), key=lambda kv: -kv[1]["without_capital"]):
        if d["without_capital"]:
            L.append(f"- **{theme}**: {d['without_capital']}/{d['total']} ({int(d['pct']*100)}%)")
    return "\n".join(L) + "\n"


def run(db_path: pathlib.Path) -> dict:
    conn = sqlite3.connect(db_path)
    theme_map = _themes(conn)
    top_stage = _startup_top_stage(conn)

    res = {
        "pyramid": stage_pyramid(conn, theme_map, top_stage),
        "cohorts": cohorts(conn, theme_map),
        "syndication": syndication(conn),
        "foreign_dependence": foreign_dependence(conn, theme_map),
        "concentration": concentration(conn, theme_map),
        "capital_gap": capital_gap(conn, theme_map, top_stage),
        "generated_at": date.today().isoformat(),
    }
    conn.close()

    write_js_global(ROOT / "pilot" / "capital-structure-data.js", "CAPITAL_STRUCTURE", res)
    (ROOT / "quality" / "capital_structure_report.md").write_text(_report(res), encoding="utf-8")

    return {
        "funded": sum(res["pyramid"]["global"].values()),
        "no_capital": res["capital_gap"]["total_without_capital"],
        "syndication_pairs": res["syndication"]["total_pairs"],
        "cohort_years": len(res["cohorts"]["by_year"]),
    }
