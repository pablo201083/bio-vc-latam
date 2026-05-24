"""
scripts/fund_gap_report.py — T1: Identifica gaps de cobertura por inversor.

Para cada inversor activo (con al menos 1 edge), calcula qué startups 'include'
comparten país y/o tema con su portfolio existente pero NO tienen edge con él.

Salida: quality/fund_gap_candidates.csv — para revisión manual del curador.

Uso:
    python scripts/fund_gap_report.py
    python scripts/fund_gap_report.py --min-portfolio 3
    python scripts/fund_gap_report.py --top-funds 15
    python scripts/fund_gap_report.py --investor kptl
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
from collections import Counter
from pathlib import Path

ROOT     = Path(__file__).resolve().parent.parent
DB_PATH  = ROOT / "db" / "bio_latam.db"
OUT_PATH = ROOT / "quality" / "fund_gap_candidates.csv"


def run(
    db_path: Path = DB_PATH,
    out_path: Path = OUT_PATH,
    min_portfolio: int = 1,
    top_funds: int = 20,
    investor_filter: str | None = None,
) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # 1. All include startups
    st_rows = conn.execute("""
        SELECT e.entity_id, e.canonical_name, e.country_code,
               sx.bio_theme_primary, sx.macro_theme, sx.data_quality_score AS quality_score,
               sx.bio_theme_secondary
        FROM entities e
        JOIN startup_extended sx ON sx.startup_id = e.entity_id
        WHERE sx.scope_decision = 'include'
          AND e.status != 'excluded'
    """).fetchall()

    startups = {
        r["entity_id"]: {
            "id":      r["entity_id"],
            "name":    r["canonical_name"],
            "country": (r["country_code"] or "").upper(),
            "theme":   r["bio_theme_primary"] or r["macro_theme"] or "",
            "theme2":  r["bio_theme_secondary"] or "",
            "quality": float(r["quality_score"] or 0),
        }
        for r in st_rows
    }

    # 2. Existing investment edges
    edges = conn.execute("SELECT investor_id, startup_id FROM investment_edges").fetchall()
    portfolio: dict[str, set[str]] = {}
    for e in edges:
        portfolio.setdefault(e["investor_id"], set()).add(e["startup_id"])

    # 3. Investor metadata
    inv_rows = conn.execute("""
        SELECT e.entity_id, e.canonical_name, e.country_code, e.website,
               i.investor_type, i.geography_focus
        FROM entities e
        JOIN investors i ON i.investor_id = e.entity_id
        WHERE e.status != 'excluded'
    """).fetchall()

    investors = {
        r["entity_id"]: {
            "id":      r["entity_id"],
            "name":    r["canonical_name"],
            "country": (r["country_code"] or "").upper(),
            "website": r["website"] or "",
            "itype":   r["investor_type"] or "",
        }
        for r in inv_rows
    }

    # 4. Build country/theme profile per investor
    def profile(inv_id):
        mapped = portfolio.get(inv_id, set())
        cc = Counter(startups[s]["country"] for s in mapped if s in startups and startups[s]["country"])
        th = Counter()
        for s in mapped:
            if s not in startups: continue
            if startups[s]["theme"]:  th[startups[s]["theme"]]  += 1
            if startups[s]["theme2"]: th[startups[s]["theme2"]] += 1
        return {"mapped": mapped, "countries": set(cc), "themes": set(th)}

    # 5. Score candidates
    COUNTRY_BONUS  = 2.0
    THEME_BONUS    = 1.5
    THEME2_BONUS   = 0.8
    QUALITY_WEIGHT = 0.3
    MIN_SCORE      = 2.0

    active = {
        k: v for k, v in investors.items()
        if len(portfolio.get(k, set())) >= min_portfolio
    }
    if investor_filter:
        active = {k: v for k, v in active.items()
                  if k == investor_filter or investor_filter.lower() in v["name"].lower()}

    sorted_inv = sorted(active.items(), key=lambda kv: -len(portfolio.get(kv[0], set())))
    if not investor_filter:
        sorted_inv = sorted_inv[:top_funds]

    rows_out: list[dict] = []
    for inv_id, inv in sorted_inv:
        p = profile(inv_id)
        for sid, st in startups.items():
            if sid in p["mapped"]: continue
            score = 0.0
            reasons = []
            if st["country"] and (st["country"] == inv["country"] or st["country"] in p["countries"]):
                score += COUNTRY_BONUS
                reasons.append(f"pais={st['country']}")
            if st["theme"] and st["theme"] in p["themes"]:
                score += THEME_BONUS
                reasons.append(f"tema_principal")
            if st["theme2"] and st["theme2"] in p["themes"]:
                score += THEME2_BONUS
            score += st["quality"] * QUALITY_WEIGHT
            if score >= MIN_SCORE:
                rows_out.append({
                    "investor_id":      inv_id,
                    "investor_name":    inv["name"],
                    "investor_country": inv["country"],
                    "investor_type":    inv["itype"],
                    "portfolio_size":   len(p["mapped"]),
                    "investor_website": inv["website"],
                    "score":            round(score, 2),
                    "startup_id":       sid,
                    "startup_name":     st["name"],
                    "startup_country":  st["country"],
                    "startup_theme":    st["theme"],
                    "quality_score":    round(st["quality"], 1),
                    "match_reason":     ";".join(reasons),
                    "confirm":          "",
                    "source_url":       "",
                })

    # Sort: highest-opportunity investors first, then score desc within each investor
    rows_out.sort(key=lambda r: (-r["portfolio_size"], -r["score"]))

    # Cap per investor at 30
    counts: dict[str, int] = {}
    capped = []
    for r in rows_out:
        k = r["investor_id"]
        if counts.get(k, 0) >= 30: continue
        counts[k] = counts.get(k, 0) + 1
        capped.append(r)

    # Write
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "investor_id","investor_name","investor_country","investor_type",
        "portfolio_size","investor_website",
        "score","startup_id","startup_name","startup_country",
        "startup_theme","quality_score","match_reason",
        "confirm","source_url",
    ]
    with out_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(capped)

    conn.close()
    top5 = Counter(r["investor_id"] for r in capped).most_common(5)
    return {
        "investors_analyzed": len(sorted_inv),
        "total_candidates": len(capped),
        "top_opportunity_funds": top5,
        "out": str(out_path),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fund gap report — T1 capital V1")
    parser.add_argument("--min-portfolio", type=int, default=1)
    parser.add_argument("--top-funds",     type=int, default=20)
    parser.add_argument("--investor",      type=str, default=None)
    parser.add_argument("--db",            type=str, default=None)
    args = parser.parse_args()

    db = Path(args.db) if args.db else DB_PATH

    print(f"\n  Fund Gap Report — BIO LATAM Capital V1")
    print(f"  DB: {db.name} | min_portfolio={args.min_portfolio} | top_funds={args.top_funds}")
    if args.investor: print(f"  Inversor: {args.investor}")
    print()

    res = run(db_path=db, min_portfolio=args.min_portfolio,
              top_funds=args.top_funds, investor_filter=args.investor)

    print(f"  Inversores analizados : {res['investors_analyzed']}")
    print(f"  Candidatos totales    : {res['total_candidates']}")
    print(f"\n  Top 5 fondos por oportunidad:")
    for inv_id, cnt in res["top_opportunity_funds"]:
        print(f"    {inv_id:<35} {cnt:>3} startups potenciales no mapeados")
    print(f"\n  Salida: {res['out']}\n")
