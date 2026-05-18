"""
scripts/fund_gap_report.py

Carril B — Cross-reference inversores activos vs startups include sin mapear.

Para cada inversor con al menos 1 edge, lista qué startups BIO include
NO están conectadas a él — candidatas potenciales si el inversor tiene
presencia en ese tema/país.

Output: quality/fund_gap_candidates.csv
  investor_id | investor_name | investor_type | portfolio_url
  candidate_startup_id | candidate_startup_name | bio_theme | country | quality_score
  match_reason

Uso:
  python scripts/fund_gap_report.py
  python scripts/fund_gap_report.py --min-quality 7.0  # solo startups de alta calidad
  python scripts/fund_gap_report.py --investor sp_ventures  # solo un inversor
"""
from __future__ import annotations

import argparse
import csv
import pathlib
import sqlite3
import sys
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT    = pathlib.Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "db" / "bio_latam.db"
OUT     = ROOT / "quality" / "fund_gap_candidates.csv"


def main(min_quality: float = 6.0, only_investor: str | None = None) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # ── Startups include con sus datos ───────────────────────────────────────
    startups = conn.execute("""
        SELECT sx.startup_id, sx.bio_theme_primary AS bio_theme,
               sx.data_quality_score,
               e.canonical_name AS name,
               e.country_code AS country,
               GROUP_CONCAT(DISTINCT e2.country_code) AS all_countries
        FROM startup_extended sx
        JOIN entities e ON e.entity_id = sx.startup_id
        LEFT JOIN entities e2 ON e2.entity_id = sx.startup_id
        WHERE sx.scope_decision = 'include'
          AND (sx.data_quality_score IS NULL OR sx.data_quality_score >= ?)
        GROUP BY sx.startup_id
        ORDER BY sx.data_quality_score DESC
    """, (min_quality,)).fetchall()
    startups = [dict(s) for s in startups]
    startup_by_id = {s["startup_id"]: s for s in startups}

    # ── Inversores activos (con al menos 1 edge) ────────────────────────────
    investor_filter = "AND i.investor_id = ?" if only_investor else ""
    inv_params = (only_investor,) if only_investor else ()

    investors = conn.execute(f"""
        SELECT i.investor_id, e.canonical_name AS investor_name,
               i.investor_type, i.geography_focus, i.vertical_focus,
               e.website,
               COUNT(DISTINCT ie.startup_id) AS n_portfolio
        FROM investors i
        JOIN entities e ON e.entity_id = i.investor_id
        JOIN investment_edges ie ON ie.investor_id = i.investor_id
        {investor_filter}
        GROUP BY i.investor_id
        ORDER BY n_portfolio DESC
    """, inv_params).fetchall()
    investors = [dict(iv) for iv in investors]

    # ── Edges existentes: inversor → set de startup_ids ─────────────────────
    all_edges = conn.execute(
        "SELECT investor_id, startup_id FROM investment_edges"
    ).fetchall()
    investor_portfolio: dict[str, set[str]] = defaultdict(set)
    for row in all_edges:
        investor_portfolio[row[0]].add(row[1])

    # ── URL de portfolio del inversor (primera URL pública de sus edges) ─────
    portfolio_urls = conn.execute("""
        SELECT ie.investor_id, s.url AS portfolio_url
        FROM investment_edges ie
        JOIN sources s ON s.source_id = ie.source_id
        WHERE s.url IS NOT NULL
        GROUP BY ie.investor_id
    """).fetchall()
    inv_url = {r[0]: r[1] for r in portfolio_urls}

    # Para inversores sin URL en sources, usar website de entities
    for iv in investors:
        if iv["investor_id"] not in inv_url and iv["website"]:
            inv_url[iv["investor_id"]] = iv["website"]

    # ── Temas y países cubiertos por cada inversor ───────────────────────────
    inv_themes: dict[str, set[str]] = defaultdict(set)
    inv_countries: dict[str, set[str]] = defaultdict(set)

    theme_country_rows = conn.execute("""
        SELECT ie.investor_id,
               sx.bio_theme_primary AS bio_theme,
               e.country_code
        FROM investment_edges ie
        JOIN startup_extended sx ON sx.startup_id = ie.startup_id
        JOIN entities e ON e.entity_id = ie.startup_id
        WHERE sx.scope_decision = 'include'
    """).fetchall()
    for row in theme_country_rows:
        if row["bio_theme"]:
            inv_themes[row["investor_id"]].add(row["bio_theme"])
        if row["country_code"]:
            inv_countries[row["investor_id"]].add(row["country_code"])

    # ── Generar candidatos ───────────────────────────────────────────────────
    rows_out = []
    for iv in investors:
        iid     = iv["investor_id"]
        covered = investor_portfolio[iid]
        themes  = inv_themes[iid]
        cntries = inv_countries[iid]
        url     = inv_url.get(iid, "")

        for s in startups:
            sid = s["startup_id"]
            if sid in covered:
                continue  # ya mapeado

            # Calcular razón de match
            reasons = []
            s_theme   = s.get("bio_theme") or ""
            s_country = s.get("country") or ""

            if s_theme and s_theme in themes:
                reasons.append(f"tema_match:{s_theme}")
            if s_country and s_country in cntries:
                reasons.append(f"pais_match:{s_country}")

            # Solo incluir si hay al menos una razón de match
            if not reasons:
                continue

            rows_out.append({
                "investor_id":         iid,
                "investor_name":       iv["investor_name"],
                "investor_type":       iv["investor_type"],
                "portfolio_url":       url,
                "candidate_startup_id":   sid,
                "candidate_startup_name": s["name"],
                "bio_theme":           s_theme,
                "country":             s_country,
                "data_quality_score":       s.get("data_quality_score") or "",
                "match_reason":        " | ".join(reasons),
                "action":              "",  # curador llena: confirm / discard / review
                "notes":               "",  # curador llena
            })

    conn.close()

    # ── Ordenar: primero por inversor (mayor portfolio), luego calidad ───────
    inv_order = {iv["investor_id"]: i for i, iv in enumerate(investors)}
    rows_out.sort(key=lambda r: (
        inv_order.get(r["investor_id"], 999),
        -(float(r["data_quality_score"]) if r["data_quality_score"] else 0)
    ))

    # ── Escribir CSV ─────────────────────────────────────────────────────────
    OUT.parent.mkdir(parents=True, exist_ok=True)
    COLS = [
        "investor_id", "investor_name", "investor_type", "portfolio_url",
        "candidate_startup_id", "candidate_startup_name",
        "bio_theme", "country", "data_quality_score",
        "match_reason", "action", "notes",
    ]
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows_out)

    # ── Resumen en consola ───────────────────────────────────────────────────
    print(f"\n  Inversores activos analizados: {len(investors)}")
    print(f"  Candidatos generados: {len(rows_out)}")

    # Top 10 inversores con más candidatos
    from collections import Counter
    by_inv = Counter(r["investor_id"] for r in rows_out)
    print("\n  Top inversores con más candidatos pendientes:")
    for iid, n in by_inv.most_common(10):
        iname = next(iv["investor_name"] for iv in investors if iv["investor_id"] == iid)
        print(f"    {n:3d}  {iname} ({iid})")

    print(f"\n  → quality/fund_gap_candidates.csv ({len(rows_out)} filas)")
    print("\n  Columna 'action': escribe 'confirm' para añadir a manual_canonical_investment_edges.csv")
    print("  Columna 'notes': evidencia de la relación (URL del portfolio, nota)\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-quality", type=float, default=6.0,
                        help="Score mínimo de calidad de startup (default 6.0)")
    parser.add_argument("--investor", type=str, default=None,
                        help="Filtrar por investor_id (ej: sp_ventures)")
    args = parser.parse_args()
    main(min_quality=args.min_quality, only_investor=args.investor)
