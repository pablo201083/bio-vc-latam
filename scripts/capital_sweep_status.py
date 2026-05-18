"""
scripts/capital_sweep_status.py

Dashboard rápido en consola del estado del grafo de capital.
Llamable directamente o vía: python pipeline.py fund-sweep-status

Muestra:
  - Cobertura global y por tema
  - Top 10 fondos activos con más startups potenciales no mapeadas
  - Top 10 startups include con mayor quality_score sin ninguna edge
  - 10 fondos inactivos con mayor potencial (presencia en temas/países del universo)
  - Estado de trazabilidad (edges con/sin source)
"""
from __future__ import annotations

import pathlib
import sqlite3
import sys
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT    = pathlib.Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "db" / "bio_latam.db"

BAR_W = 28  # ancho de barras en consola

TARGETS = {
    "startups_funded_pct": 80.0,
    "edges_total":         700,
    "investors_active":    65,
    "null_source_pct":     7.0,
}


def bar(pct: float, width: int = BAR_W, fill: str = "█", empty: str = "░") -> str:
    filled = round(pct / 100 * width)
    return fill * filled + empty * (width - filled)


def run(db_path: pathlib.Path = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # ── Métricas globales ────────────────────────────────────────────────────
    total_inc = conn.execute(
        "SELECT COUNT(*) FROM startup_extended WHERE scope_decision='include'"
    ).fetchone()[0]
    funded = conn.execute("""
        SELECT COUNT(DISTINCT ie.startup_id) FROM investment_edges ie
        JOIN startup_extended sx ON sx.startup_id = ie.startup_id
        WHERE sx.scope_decision = 'include'
    """).fetchone()[0]
    edges_total = conn.execute("SELECT COUNT(*) FROM investment_edges").fetchone()[0]
    null_src = conn.execute(
        "SELECT COUNT(*) FROM investment_edges WHERE source_id IS NULL"
    ).fetchone()[0]
    investors_active = conn.execute(
        "SELECT COUNT(DISTINCT investor_id) FROM investment_edges"
    ).fetchone()[0]
    with_date = conn.execute(
        "SELECT COUNT(*) FROM investment_edges WHERE announced_date IS NOT NULL"
    ).fetchone()[0]
    with_amount = conn.execute(
        "SELECT COUNT(*) FROM investment_edges WHERE amount IS NOT NULL"
    ).fetchone()[0]

    funded_pct  = funded / total_inc * 100 if total_inc else 0
    null_pct    = null_src / edges_total * 100 if edges_total else 0
    date_pct    = with_date / edges_total * 100 if edges_total else 0
    amount_pct  = with_amount / edges_total * 100 if edges_total else 0

    sep = "─" * 62

    print(f"\n{'─'*62}")
    print("  CAPITAL GRAPH — SWEEP STATUS")
    print(sep)
    print(f"  {'Metric':<34} {'Actual':>7}  {'Target':>7}  {'Status'}")
    print(sep)

    def metric_row(label, actual, target, fmt="{:.1f}%", higher_better=True):
        a_str = fmt.format(actual) if "{" in fmt else str(actual)
        t_str = fmt.format(target) if "{" in fmt else str(target)
        if higher_better:
            ok = actual >= target
        else:
            ok = actual <= target
        status = "OK" if ok else "GAP"
        flag   = "" if ok else " <--"
        print(f"  {label:<34} {a_str:>7}  {t_str:>7}  {status}{flag}")

    metric_row("Startups include con capital (%)", funded_pct,    TARGETS["startups_funded_pct"])
    metric_row("Edges totales",                    edges_total,   TARGETS["edges_total"],    "{:.0f}", True)
    metric_row("Inversores activos",               investors_active, TARGETS["investors_active"], "{:.0f}", True)
    metric_row("Edges sin source (%)",             null_pct,      TARGETS["null_source_pct"],  "{:.1f}%", False)
    metric_row("Edges con fecha (%)",              date_pct,      30.0)
    metric_row("Edges con monto (%)",              amount_pct,    15.0)

    print(sep)
    print(f"  Startups: {funded}/{total_inc} financiadas  |  {total_inc-funded} sin edge")
    print(f"  Source NULL: {null_src}/{edges_total}  |  Con fecha: {with_date}  |  Con monto: {with_amount}")

    # ── Cobertura por tema ───────────────────────────────────────────────────
    theme_rows = conn.execute("""
        SELECT sx.bio_theme_primary AS theme,
               COUNT(*) AS total,
               SUM(CASE WHEN ie.startup_id IS NOT NULL THEN 1 ELSE 0 END) AS funded
        FROM startup_extended sx
        LEFT JOIN (
            SELECT DISTINCT startup_id FROM investment_edges
        ) ie ON ie.startup_id = sx.startup_id
        WHERE sx.scope_decision = 'include' AND sx.bio_theme_primary IS NOT NULL
        GROUP BY sx.bio_theme_primary
        ORDER BY funded * 1.0 / COUNT(*) DESC
    """).fetchall()

    print(f"\n{'─'*62}")
    print("  COBERTURA POR TEMA")
    print(sep)
    for r in theme_rows:
        pct  = r["funded"] / r["total"] * 100 if r["total"] else 0
        name = (r["theme"] or "?")[:32]
        b    = bar(pct, 20)
        print(f"  {name:<32} {b} {r['funded']:3}/{r['total']:3} {pct:5.1f}%")

    # ── Top 10 startups sin edge, mayor quality ──────────────────────────────
    unfunded_top = conn.execute("""
        SELECT sx.startup_id, e.canonical_name AS name,
               sx.bio_theme_primary AS theme, e.country_code AS country,
               sx.data_quality_score
        FROM startup_extended sx
        JOIN entities e ON e.entity_id = sx.startup_id
        LEFT JOIN investment_edges ie ON ie.startup_id = sx.startup_id
        WHERE sx.scope_decision = 'include' AND ie.startup_id IS NULL
          AND sx.data_quality_score IS NOT NULL
        ORDER BY sx.data_quality_score DESC
        LIMIT 10
    """).fetchall()

    print(f"\n{'─'*62}")
    print("  TOP 10 STARTUPS SIN EDGE (mayor quality_score)")
    print(sep)
    print(f"  {'Startup':<28} {'Tema':<22} {'País':>4}  Score")
    print(sep)
    for r in unfunded_top:
        name    = (r["name"] or r["startup_id"] or "?")[:27]
        theme   = (r["theme"] or "?")[:21]
        country = (r["country"] or "?")
        score   = f"{r["data_quality_score"]:.1f}" if r["data_quality_score"] else "—"
        print(f"  {name:<28} {theme:<22} {country:>4}  {score}")

    # ── Top 10 inversores activos con más gaps posibles (por tema/país) ──────
    # "Gaps potenciales" = startups include sin edge CON mismo tema/país que el inversor cubre
    inv_portfolio = defaultdict(set)
    inv_themes    = defaultdict(set)
    inv_countries = defaultdict(set)
    for row in conn.execute("""
        SELECT ie.investor_id, ie.startup_id,
               sx.bio_theme_primary AS theme, e.country_code AS country
        FROM investment_edges ie
        JOIN startup_extended sx ON sx.startup_id = ie.startup_id
        JOIN entities e ON e.entity_id = ie.startup_id
        WHERE sx.scope_decision = 'include'
    """).fetchall():
        inv_portfolio[row["investor_id"]].add(row["startup_id"])
        if row["theme"]:   inv_themes[row["investor_id"]].add(row["theme"])
        if row["country"]: inv_countries[row["investor_id"]].add(row["country"])

    unfunded_all = conn.execute("""
        SELECT sx.startup_id, sx.bio_theme_primary AS theme,
               e.country_code AS country, sx.data_quality_score
        FROM startup_extended sx
        JOIN entities e ON e.entity_id = sx.startup_id
        LEFT JOIN investment_edges ie ON ie.startup_id = sx.startup_id
        WHERE sx.scope_decision = 'include' AND ie.startup_id IS NULL
    """).fetchall()
    unfunded_all = [dict(r) for r in unfunded_all]

    inv_names = {r[0]: r[1] for r in conn.execute(
        "SELECT i.investor_id, e.canonical_name FROM investors i JOIN entities e ON e.entity_id=i.investor_id"
    ).fetchall()}

    gap_counts: dict[str, int] = defaultdict(int)
    for iid in inv_portfolio:
        for s in unfunded_all:
            if s["theme"] in inv_themes[iid] or s["country"] in inv_countries[iid]:
                gap_counts[iid] += 1

    top_gap_inv = sorted(gap_counts.items(), key=lambda x: -x[1])[:10]

    print(f"\n{'─'*62}")
    print("  TOP 10 INVERSORES ACTIVOS POR GAPS POTENCIALES")
    print(f"  (startups sin edge con mismo tema/país que ya cubren)")
    print(sep)
    print(f"  {'Inversor':<30} {'Portfolio':>9}  {'Gaps pot.':>9}")
    print(sep)
    for iid, n_gaps in top_gap_inv:
        iname = inv_names.get(iid, iid)[:29]
        port  = len(inv_portfolio[iid])
        print(f"  {iname:<30} {port:>9}  {n_gaps:>9}")

    # ── Inversores INACTIVOS — Carril A ──────────────────────────────────────
    TYPE_PRIORITY = {
        "multilateral": 0, "development_finance": 1, "vc": 2,
        "impact_fund": 3, "accelerator": 4, "corporate_vc": 5,
        "association": 6, "investor": 7,
    }
    inactive_all = conn.execute("""
        SELECT i.investor_id, e.canonical_name AS name, i.investor_type,
               e.website, e.country_code, i.geography_focus, i.vertical_focus
        FROM investors i
        JOIN entities e ON e.entity_id = i.investor_id
        WHERE i.investor_id NOT IN (SELECT DISTINCT investor_id FROM investment_edges)
        ORDER BY e.canonical_name
    """).fetchall()
    inactive_all = sorted(inactive_all,
        key=lambda r: TYPE_PRIORITY.get(r["investor_type"] or "", 99))

    print(f"\n{'─'*62}")
    print(f"  CARRIL A — {len(inactive_all)} INVERSORES INACTIVOS (sin ninguna edge)")
    print(f"  Prioridad: multilateral/DFI > VC > impact fund > aceleradora")
    print(sep)
    print(f"  {'Inversor':<28} {'Tipo':<14} {'País'} {'Website'}")
    print(sep)
    for r in inactive_all:
        name = (r["name"] or r["investor_id"])[:27]
        tipo = (r["investor_type"] or "?")[:13]
        pais = (r["country_code"] or "—")[:3]
        site = (r["website"] or "—")[:38]
        marker = " *" if r["website"] else "  "
        print(f" {marker}{name:<28} {tipo:<14} {pais:<4} {site}")

    # ── Edges sin source (Carril C) ──────────────────────────────────────────
    no_src_top = conn.execute("""
        SELECT ie.investor_id, e.canonical_name AS investor_name,
               COUNT(*) AS n
        FROM investment_edges ie
        JOIN entities e ON e.entity_id = ie.investor_id
        WHERE ie.source_id IS NULL
        GROUP BY ie.investor_id
        ORDER BY n DESC
        LIMIT 8
    """).fetchall()

    print(f"\n{'─'*62}")
    print(f"  EDGES SIN SOURCE_ID — {null_src} total (Carril C — fix trazabilidad)")
    print(sep)
    for r in no_src_top:
        print(f"  {(r['investor_name'] or r['investor_id']):<30} {r['n']:>4} edges sin source")

    print(f"\n{'─'*62}")
    print("  WORKFLOW DE CURACIÓN")
    print(sep)
    print("  CARRIL A — Sweep de inversores inactivos:")
    print("    1. Visitar portfolio page del inversor (ver lista arriba)")
    print("    2. Llenar staging/capital_intake.csv:")
    print("       investor_id | startup_name | round_stage | source_url")
    print("    3. python pipeline.py ingest-intake  (canoniza + rebuild + atlas)")
    print()
    print("  CARRIL B — Cross-check inversores activos:")
    print("    1. python scripts/fund_gap_report.py  # genera quality/fund_gap_candidates.csv")
    print("    2. Abrir CSV, columna 'action' = confirm para las que son reales")
    print("    3. Copiar las confirmadas a staging/capital_intake.csv")
    print("    4. python pipeline.py ingest-intake")
    print(f"{'─'*62}\n")

    conn.close()


if __name__ == "__main__":
    run()
